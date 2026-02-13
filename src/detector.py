"""Object Detection Module - YOLOv11 for person/object detection"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class ObjectDetector:
    """YOLO-based object detector optimized for surveillance"""
    
    def __init__(self, model_path: str = "yolo11n.pt", conf_threshold: float = 0.5):
        self.conf_threshold = conf_threshold
        self.model = None
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            logger.info(f"Loaded YOLO model: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            raise
    
    def detect(self, image_path: Path) -> List[Dict]:
        """
        Detect objects in image
        
        Returns:
            List of detections with keys: class, confidence, bbox
        """
        if not self.model:
            return []
        
        try:
            results = self.model(str(image_path), conf=self.conf_threshold)
            detections = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    detection = {
                        "class": result.names[int(box.cls)],
                        "confidence": float(box.conf),
                        "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    }
                    detections.append(detection)
            
            return detections
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def detect_person(self, image_path: Path) -> bool:
        """Quick check if person is in image"""
        detections = self.detect(image_path)
        return any(d["class"] == "person" for d in detections)
    
    def get_person_count(self, image_path: Path) -> int:
        """Count number of people in image"""
        detections = self.detect(image_path)
        return sum(1 for d in detections if d["class"] == "person")


if __name__ == "__main__":
    # Test
    detector = ObjectDetector()
    test_image = Path("/Volumes/disco1tb/video-surv/highfreq/2026-02-13/sala/190000.jpg")
    if test_image.exists():
        detections = detector.detect(test_image)
        print(f"Found {len(detections)} objects:")
        for d in detections:
            print(f"  - {d['class']}: {d['confidence']:.2f}")
