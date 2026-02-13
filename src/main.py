"""VigilHome Main Orchestrator - Integrates all components"""
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, MODELS_DIR, CAMERAS, FEATURES, TELEGRAM_CONFIG
from detector import ObjectDetector
from scene_understanding import SceneUnderstanding
from behavioral_analyzer import BehavioralAnalyzer
from semantic_search import SemanticSearch, create_search_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VigilHome:
    """
    Main orchestrator for VigilHome AI surveillance system.
    
    Integrates:
    - Object Detection (YOLOv11)
    - Scene Understanding (VLM)
    - Behavioral Analysis
    - Semantic Search
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize VigilHome system.
        
        Args:
            data_dir: Base directory for data storage
        """
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.models_dir = MODELS_DIR
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(exist_ok=True)
        
        # Initialize components
        self.detector: Optional[ObjectDetector] = None
        self.scene_understanding: Optional[SceneUnderstanding] = None
        self.behavioral_analyzer: Optional[BehavioralAnalyzer] = None
        self.semantic_search: Optional[SemanticSearch] = None
        
        self._init_components()
        
        logger.info("VigilHome initialized successfully")
    
    def _init_components(self):
        """Initialize all AI components"""
        # Object Detection
        try:
            model_path = self.models_dir / "yolo11n.pt"
            if not model_path.exists():
                model_path = "yolo11n.pt"  # Use default
            self.detector = ObjectDetector(model_path=str(model_path))
            logger.info("Object detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize detector: {e}")
        
        # Scene Understanding
        if FEATURES.get("scene_understanding", True):
            try:
                self.scene_understanding = SceneUnderstanding()
                logger.info("Scene understanding initialized")
            except Exception as e:
                logger.error(f"Failed to initialize scene understanding: {e}")
        
        # Behavioral Analyzer
        if FEATURES.get("behavioral_baseline", True):
            try:
                behavioral_data_dir = self.data_dir / "behavioral"
                self.behavioral_analyzer = BehavioralAnalyzer(behavioral_data_dir)
                logger.info("Behavioral analyzer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize behavioral analyzer: {e}")
        
        # Semantic Search
        if FEATURES.get("semantic_search", True):
            try:
                search_data_dir = self.data_dir / "semantic_search"
                self.semantic_search = create_search_engine(search_data_dir)
                logger.info("Semantic search initialized")
            except Exception as e:
                logger.error(f"Failed to initialize semantic search: {e}")
    
    def process_frame(self, image_path: Path, camera: str,
                     timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Process a single frame through the entire pipeline.
        
        Args:
            image_path: Path to image file
            camera: Camera identifier
            timestamp: Frame timestamp (defaults to now)
        
        Returns:
            Processing results dict
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        results = {
            "timestamp": timestamp.isoformat(),
            "camera": camera,
            "image_path": str(image_path),
            "detections": [],
            "description": None,
            "anomaly": None,
            "event_id": None
        }
        
        # Step 1: Object Detection
        if self.detector and image_path.exists():
            try:
                detections = self.detector.detect(image_path)
                results["detections"] = detections
                logger.debug(f"Detected {len(detections)} objects in {camera}")
            except Exception as e:
                logger.error(f"Detection failed: {e}")
        
        # Step 2: Scene Understanding
        if self.scene_understanding and image_path.exists():
            try:
                context = {
                    "camera": camera,
                    "time": timestamp.strftime("%H:%M"),
                    "detections": results["detections"]
                }
                description = self.scene_understanding.describe_with_objects(
                    image_path, results["detections"]
                )
                results["description"] = description
                logger.debug(f"Scene description: {description[:50]}...")
            except Exception as e:
                logger.error(f"Scene understanding failed: {e}")
        
        # Step 3: Behavioral Analysis
        if self.behavioral_analyzer:
            try:
                # Record movement for each person detection
                for det in results["detections"]:
                    if det.get("class") == "person":
                        event = self.behavioral_analyzer.record_movement(
                            camera=camera,
                            bbox=det["bbox"],
                            confidence=det["confidence"],
                            timestamp=timestamp
                        )
                        
                        # Check for anomalies
                        anomaly = self.behavioral_analyzer.detect_anomaly(event)
                        if anomaly:
                            results["anomaly"] = anomaly
                            logger.warning(f"Anomaly detected: {anomaly['type']}")
            except Exception as e:
                logger.error(f"Behavioral analysis failed: {e}")
        
        # Step 4: Index for Semantic Search
        if self.semantic_search and results["description"]:
            try:
                event_id = self.semantic_search.index_event(
                    timestamp=timestamp,
                    camera=camera,
                    image_path=image_path,
                    description=results["description"],
                    detections=results["detections"],
                    confidence=0.9
                )
                results["event_id"] = event_id
                logger.debug(f"Indexed event {event_id}")
            except Exception as e:
                logger.error(f"Semantic indexing failed: {e}")
        
        return results
    
    def search_events(self, query: str, **kwargs) -> list:
        """
        Search events using natural language.
        
        Args:
            query: Natural language query
            **kwargs: Additional search parameters
        
        Returns:
            List of matching events
        """
        if self.semantic_search:
            return self.semantic_search.search(query, **kwargs)
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {
            "components": {
                "detector": self.detector is not None,
                "scene_understanding": self.scene_understanding is not None,
                "behavioral_analyzer": self.behavioral_analyzer is not None,
                "semantic_search": self.semantic_search is not None
            },
            "features_enabled": FEATURES
        }
        
        if self.semantic_search:
            stats["search"] = self.semantic_search.get_stats()
        
        if self.behavioral_analyzer:
            stats["behavioral"] = {
                "has_sufficient_baseline": self.behavioral_analyzer.has_sufficient_baseline(),
                "total_events": len(self.behavioral_analyzer.events)
            }
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Run system health check"""
        checks = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        # Check detector
        if self.detector:
            checks["checks"]["detector"] = "ok"
        else:
            checks["checks"]["detector"] = "failed"
            checks["status"] = "degraded"
        
        # Check scene understanding
        if self.scene_understanding:
            checks["checks"]["scene_understanding"] = "ok"
        else:
            checks["checks"]["scene_understanding"] = "disabled"
        
        # Check behavioral analyzer
        if self.behavioral_analyzer:
            baseline_ok = self.behavioral_analyzer.has_sufficient_baseline()
            checks["checks"]["behavioral"] = "ready" if baseline_ok else "collecting_data"
        else:
            checks["checks"]["behavioral"] = "disabled"
        
        # Check semantic search
        if self.semantic_search:
            search_stats = self.semantic_search.get_stats()
            checks["checks"]["semantic_search"] = "ok"
            checks["checks"]["indexed_events"] = search_stats.get("total_events", 0)
        else:
            checks["checks"]["semantic_search"] = "disabled"
        
        return checks


def run_test():
    """Run end-to-end test"""
    print("=" * 60)
    print("VigilHome End-to-End Test")
    print("=" * 60)
    
    # Initialize system
    vigil = VigilHome()
    
    # Health check
    print("\n1. Health Check:")
    health = vigil.health_check()
    print(f"   Status: {health['status']}")
    for check, status in health['checks'].items():
        print(f"   - {check}: {status}")
    
    # Test on sample images
    test_dir = Path("/Volumes/disco1tb/video-surv/highfreq/2026-02-13")
    test_images = []
    
    if test_dir.exists():
        for camera in ["sala", "cozinha"]:
            camera_dir = test_dir / camera
            if camera_dir.exists():
                images = list(camera_dir.glob("*.jpg"))[:2]  # First 2 from each
                for img in images:
                    test_images.append((camera, img))
    
    if not test_images:
        print("\n⚠️  No test images found!")
        return
    
    print(f"\n2. Processing {len(test_images)} test images...")
    results = []
    
    for camera, image_path in test_images:
        print(f"\n   Processing: {camera}/{image_path.name}")
        
        result = vigil.process_frame(image_path, camera)
        results.append(result)
        
        # Print results
        print(f"   - Detections: {len(result['detections'])}")
        if result['detections']:
            for det in result['detections'][:3]:  # Show first 3
                print(f"     • {det['class']}: {det['confidence']:.2f}")
        
        if result['description']:
            print(f"   - Description: {result['description'][:60]}...")
        
        if result['anomaly']:
            print(f"   - ⚠️ Anomaly: {result['anomaly']['message']}")
        
        if result['event_id']:
            print(f"   - Indexed: {result['event_id'][:8]}...")
    
    # Test search
    print("\n3. Testing Semantic Search:")
    if vigil.semantic_search:
        search_results = vigil.search_events("person in room", n_results=3)
        print(f"   Found {len(search_results)} results for 'person in room'")
        for r in search_results[:2]:
            print(f"   - [{r['similarity']:.2f}] {r['description'][:50]}...")
    else:
        print("   Search not available")
    
    # Stats
    print("\n4. System Stats:")
    stats = vigil.get_stats()
    print(f"   Components: {stats['components']}")
    if 'search' in stats:
        print(f"   Indexed events: {stats['search'].get('total_events', 0)}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    run_test()
