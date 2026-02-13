"""
VigilHome Real-Time Detection & Alerts Daemon

Continuously monitors captured images and sends Telegram alerts when people are detected.
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Set, Dict, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/vigilhome_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from detector import ObjectDetector
from scene_understanding import SceneUnderstanding
from behavioral_analyzer import BehavioralAnalyzer, MovementEvent


class RealtimeMonitor:
    """Real-time surveillance monitor with YOLO detection and Telegram alerts"""
    
    def __init__(self, 
                 captures_dir: str = "/Volumes/disco1tb/video-surv/highfreq/2026-02-13/",
                 data_dir: str = "/Users/augustosilva/clawd/projects/video-surveillance-rnd/data",
                 conf_threshold: float = 0.5,
                 rate_limit_seconds: int = 30,
                 status_interval_minutes: int = 5):
        
        self.captures_dir = Path(captures_dir)
        self.data_dir = Path(data_dir)
        self.conf_threshold = conf_threshold
        self.rate_limit_seconds = rate_limit_seconds
        self.status_interval = timedelta(minutes=status_interval_minutes)
        
        # State tracking
        self.processed_images: Set[str] = set()
        self.last_alert_time: Dict[str, datetime] = {}
        self.stats = {
            "images_processed": 0,
            "persons_detected": 0,
            "alerts_sent": 0,
            "errors": 0
        }
        
        # Initialize components
        logger.info("Initializing VigilHome Real-Time Monitor...")
        logger.info(f"Captures directory: {self.captures_dir}")
        
        try:
            self.detector = ObjectDetector(
                model_path="/Users/augustosilva/clawd/projects/video-surveillance-rnd/yolo11n.pt",
                conf_threshold=self.conf_threshold
            )
            logger.info("✅ Object detector loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load detector: {e}")
            raise
        
        try:
            self.scene = SceneUnderstanding()
            logger.info("✅ Scene understanding loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load scene understanding: {e}")
            self.scene = None
        
        try:
            self.analyzer = BehavioralAnalyzer(self.data_dir, min_baseline_days=0)
            logger.info("✅ Behavioral analyzer loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load behavioral analyzer: {e}")
            self.analyzer = None
        
        self.last_status_time = datetime.now()
        logger.info("🚀 VigilHome Monitor initialized successfully")
    
    def get_camera_dirs(self) -> list:
        """Get list of camera directories"""
        if not self.captures_dir.exists():
            logger.error(f"Captures directory does not exist: {self.captures_dir}")
            return []
        
        return [d for d in self.captures_dir.iterdir() if d.is_dir()]
    
    def get_new_images(self, camera_dir: Path) -> list:
        """Get new images from camera directory that haven't been processed"""
        if not camera_dir.exists():
            return []
        
        new_images = []
        for img_path in camera_dir.glob("*.jpg"):
            img_str = str(img_path)
            if img_str not in self.processed_images:
                new_images.append(img_path)
        
        # Sort by modification time (newest first)
        new_images.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return new_images
    
    def check_rate_limit(self, camera: str) -> bool:
        """Check if we can send alert for this camera (rate limiting)"""
        now = datetime.now()
        last_alert = self.last_alert_time.get(camera)
        
        if last_alert is None:
            return True
        
        elapsed = (now - last_alert).total_seconds()
        return elapsed >= self.rate_limit_seconds
    
    def send_telegram_alert(self, camera: str, image_path: Path, person_count: int, description: str):
        """Send Telegram alert using OpenClaw message tool"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            message = f"🚶 PESSOA DETETADA\n"
            message += f"📍 Câmara: {camera}\n"
            message += f"🕐 Hora: {timestamp}\n"
            message += f"👥 Count: {person_count}\n"
            message += f"📝 {description}"
            
            # Use OpenClaw message tool
            # Note: This will be called from the main agent context
            alert_data = {
                "action": "send",
                "target": "-5291006422",
                "message": message,
                "media": str(image_path)
            }
            
            # Log the alert for now - actual sending happens via message tool
            logger.info(f"📤 Telegram alert queued for {camera}")
            logger.info(f"   Message: {message[:100]}...")
            
            # Store alert for batch processing
            self.pending_alerts.append(alert_data)
            
            self.last_alert_time[camera] = datetime.now()
            self.stats["alerts_sent"] += 1
            
        except Exception as e:
            logger.error(f"Failed to queue alert: {e}")
    
    def process_image(self, image_path: Path, camera: str) -> bool:
        """Process a single image for person detection"""
        try:
            # Run detection
            detections = self.detector.detect(image_path)
            
            # Filter for persons with confidence > threshold
            persons = [d for d in detections 
                      if d["class"] == "person" and d["confidence"] > self.conf_threshold]
            
            if not persons:
                return False
            
            person_count = len(persons)
            logger.info(f"🚶 Person detected in {camera}: {person_count} person(s)")
            
            # Generate scene description
            description = "Pessoa detetada na área de vigilância"
            if self.scene:
                try:
                    context = {"camera": camera, "time": datetime.now().strftime("%H:%M:%S")}
                    description = self.scene.describe_with_objects(image_path, detections)
                    logger.info(f"📝 Scene description: {description}")
                except Exception as e:
                    logger.warning(f"Scene description failed: {e}")
            
            # Log to behavioral analyzer
            if self.analyzer:
                try:
                    for person in persons:
                        event = self.analyzer.record_movement(
                            camera=camera,
                            bbox=person["bbox"],
                            confidence=person["confidence"],
                            timestamp=datetime.now()
                        )
                        # Check for anomalies
                        anomaly = self.analyzer.detect_anomaly(event)
                        if anomaly:
                            logger.warning(f"⚠️ Anomaly detected: {anomaly}")
                except Exception as e:
                    logger.warning(f"Behavioral analysis failed: {e}")
            
            # Send alert if rate limit allows
            if self.check_rate_limit(camera):
                self.send_telegram_alert(camera, image_path, person_count, description)
            else:
                logger.info(f"⏱️ Rate limit active for {camera}, skipping alert")
            
            self.stats["persons_detected"] += person_count
            return True
            
        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")
            self.stats["errors"] += 1
            return False
    
    def send_status_report(self):
        """Send periodic status report"""
        try:
            uptime = datetime.now() - self.start_time if hasattr(self, 'start_time') else timedelta(0)
            
            message = "📊 *VigilHome Status Report*\n\n"
            message += f"⏱️ Uptime: {uptime.total_seconds()/60:.1f} min\n"
            message += f"📸 Images processed: {self.stats['images_processed']}\n"
            message += f"🚶 Persons detected: {self.stats['persons_detected']}\n"
            message += f"📤 Alerts sent: {self.stats['alerts_sent']}\n"
            message += f"❌ Errors: {self.stats['errors']}\n\n"
            message += "_Monitor running normally_ ✅"
            
            logger.info(f"Status report: {message}")
            
            # Add to pending alerts
            self.pending_alerts.append({
                "action": "send",
                "target": "-5291006422",
                "message": message
            })
            
        except Exception as e:
            logger.error(f"Failed to send status report: {e}")
    
    def check_status_report(self):
        """Check if it's time to send a status report"""
        now = datetime.now()
        if now - self.last_status_time >= self.status_interval:
            self.send_status_report()
            self.last_status_time = now
    
    def run_cycle(self):
        """Run one monitoring cycle"""
        self.pending_alerts = []
        
        camera_dirs = self.get_camera_dirs()
        if not camera_dirs:
            logger.warning("No camera directories found")
            return []
        
        for camera_dir in camera_dirs:
            camera = camera_dir.name
            new_images = self.get_new_images(camera_dir)
            
            for img_path in new_images:
                # Mark as processed immediately to avoid reprocessing
                self.processed_images.add(str(img_path))
                self.stats["images_processed"] += 1
                
                # Process the image
                self.process_image(img_path, camera)
        
        # Check for status report
        self.check_status_report()
        
        return self.pending_alerts
    
    def run_forever(self, interval_seconds: int = 10):
        """Run the monitor indefinitely"""
        self.start_time = datetime.now()
        logger.info(f"🚀 Starting VigilHome Monitor (interval: {interval_seconds}s)")
        
        try:
            while True:
                alerts = self.run_cycle()
                
                # Process any pending alerts
                for alert in alerts:
                    try:
                        # Import here to avoid circular dependencies
                        import subprocess
                        result = subprocess.run(
                            ["openclaw", "message", "send", 
                             "--target", alert["target"],
                             "--message", alert["message"]] +
                            (["--media", alert["media"]] if "media" in alert else []),
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if result.returncode == 0:
                            logger.info("✅ Alert sent successfully")
                        else:
                            logger.error(f"Failed to send alert: {result.stderr}")
                    except Exception as e:
                        logger.error(f"Alert sending error: {e}")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user")
        except Exception as e:
            logger.error(f"Monitor crashed: {e}", exc_info=True)
            raise


def main():
    """Main entry point"""
    monitor = RealtimeMonitor()
    monitor.run_forever(interval_seconds=10)


if __name__ == "__main__":
    main()
