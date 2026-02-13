#!/usr/bin/env python3
"""Text-Only Detection Monitor - Smart alerts without images"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent))

from detector import ObjectDetector
from smart_alerts import SmartAlertManager
from config import DATA_DIR
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextOnlyMonitor:
    """Monitor cameras and send text-only alerts"""
    
    def __init__(self):
        self.detector = ObjectDetector()
        self.alert_manager = SmartAlertManager(
            config_path=Path(__file__).parent.parent / "config" / "alerts_config.yaml",
            telegram_notifier=None
        )
        self.running = True
        
    def __init__(self):
        self.detector = ObjectDetector()
        self.alert_manager = SmartAlertManager(
            config_path=Path(__file__).parent.parent / "config" / "alerts_config.yaml",
            telegram_notifier=None
        )
        self.running = True
        self.last_alert_time = {}  # Track last alert per camera
        self.person_present = {}   # Track if person is currently present
        
    async def monitor_camera(self, camera_name: str, image_dir: Path):
        """Monitor a single camera for new images"""
        last_processed = None
        
        while self.running:
            try:
                # Get latest image
                images = sorted(image_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)
                
                if images:
                    latest = images[0]
                    
                    if latest != last_processed:
                        last_processed = latest
                        
                        # Detect
                        detections = self.detector.detect(latest)
                        people = [d for d in detections if d['class'] == 'person']
                        
                        current_time = datetime.now()
                        has_people = len(people) > 0
                        
                        # Deduplication logic
                        last_alert = self.last_alert_time.get(camera_name, datetime.min)
                        time_since_alert = (current_time - last_alert).total_seconds()
                        was_present = self.person_present.get(camera_name, False)
                        
                        if has_people and not was_present:
                            # NEW PERSON ARRIVED - Send alert
                            if time_since_alert > 60:  # Min 60s between alerts
                                person_name = self._guess_person(camera_name, len(people))
                                msg = f"🚶 {person_name} chegou à {camera_name} ({current_time.strftime('%H:%M')})"
                                await self._send_telegram(msg)
                                logger.info(msg)
                                self.last_alert_time[camera_name] = current_time
                            self.person_present[camera_name] = True
                            
                        elif not has_people and was_present:
                            # PERSON LEFT
                            msg = f"👋 Pessoa saiu de {camera_name} ({current_time.strftime('%H:%M')})"
                            await self._send_telegram(msg)
                            logger.info(msg)
                            self.person_present[camera_name] = False
                            self.last_alert_time[camera_name] = current_time
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring {camera_name}: {e}")
                await asyncio.sleep(10)
    
    def _guess_person(self, camera: str, count: int) -> str:
        """Simple person identification based on time/context"""
        hour = datetime.now().hour
        
        # Very simple heuristic - would be replaced by face recognition
        if 18 <= hour <= 23:
            return "Augusto"  # Most likely
        elif 14 <= hour <= 17:
            return "Sofia ou Maria Rita"
        else:
            return f"{count} pessoa" if count == 1 else f"{count} pessoas"
    
    async def _send_telegram(self, message: str):
        """Send text message to Telegram"""
        try:
            # Use OpenClaw's message tool via system call
            import subprocess
            cmd = f'openclaw message send --target "-5291006422" --message "{message}"'
            subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send Telegram: {e}")
    
    async def run(self):
        """Run monitors for all cameras"""
        logger.info("Starting Text-Only Monitor...")
        
        base_dir = DATA_DIR / "highfreq" / datetime.now().strftime("%Y-%m-%d")
        
        tasks = []
        for camera in ["sala", "cozinha"]:
            cam_dir = base_dir / camera
            if cam_dir.exists():
                tasks.append(self.monitor_camera(camera, cam_dir))
        
        if tasks:
            await asyncio.gather(*tasks)
        else:
            logger.error("No camera directories found")
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    monitor = TextOnlyMonitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        monitor.stop()
        print("\nMonitor stopped")
