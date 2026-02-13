"""Quality Filter for Detections - Remove low-value alerts"""
import re
from typing import Dict, List

class QualityFilter:
    """Filter out low-quality detections to reduce noise"""
    
    # Keywords that indicate low-quality/blurry detections
    LOW_QUALITY_KEYWORDS = [
        "blur", "blurry", "blurred", "unclear", "fuzzy",
        "dark", "too dark", "obscured", "hidden",
        "silhouette", "shadow", "uncertain"
    ]
    
    # Minimum confidence threshold
    MIN_CONFIDENCE = 0.6
    
    @classmethod
    def is_quality_detection(cls, detection: Dict) -> bool:
        """
        Check if detection is high-quality enough to alert
        
        Returns:
            True if detection should generate alert
        """
        # Check confidence
        confidence = detection.get("confidence", 0)
        if confidence < cls.MIN_CONFIDENCE:
            return False
        
        # Check description for quality issues
        description = detection.get("description", "").lower()
        
        for keyword in cls.LOW_QUALITY_KEYWORDS:
            if keyword in description:
                return False
        
        return True
    
    @classmethod
    def filter_detections(cls, detections: List[Dict]) -> List[Dict]:
        """Filter list of detections, keeping only high-quality ones"""
        return [d for d in detections if cls.is_quality_detection(d)]
    
    @classmethod
    def get_filter_reason(cls, detection: Dict) -> str:
        """Get reason why detection was filtered (for logging)"""
        confidence = detection.get("confidence", 0)
        if confidence < cls.MIN_CONFIDENCE:
            return f"low_confidence ({confidence:.2f})"
        
        description = detection.get("description", "").lower()
        for keyword in cls.LOW_QUALITY_KEYWORDS:
            if keyword in description:
                return f"low_quality_keyword ({keyword})"
        
        return "unknown"
