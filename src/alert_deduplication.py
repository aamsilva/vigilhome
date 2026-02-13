"""Alert Deduplication - Reduce repetitive alerts"""
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from dataclasses import dataclass, field

@dataclass
class DetectionState:
    """Track state of detections to avoid repetition"""
    person_name: str
    objects: Set[str] = field(default_factory=set)
    last_seen: datetime = field(default_factory=datetime.now)
    alert_count: int = 0

class AlertDeduplicator:
    """
    Prevent repetitive alerts for the same person/object
    
    Strategy:
    - Track who/what is currently in each camera view
    - Only alert when NEW person/object appears
    - Alert again when person/object leaves and returns
    """
    
    def __init__(self, cooldown_seconds: int = 300):
        """
        Args:
            cooldown_seconds: Time before considering same person as "new" (default 5 min)
        """
        self.cooldown = cooldown_seconds
        self.active_detections: Dict[str, DetectionState] = {}  # camera -> state
        self.last_alert_time: Dict[str, datetime] = {}  # key -> time
    
    def should_alert(self, camera: str, person: str, objects: list) -> bool:
        """
        Check if this detection should trigger an alert
        
        Returns:
            True if new person/object detected or significant change
        """
        current_time = datetime.now()
        key = f"{camera}:{person}"
        
        # Convert objects to set for comparison
        current_objects = set(obj['class'] for obj in objects if obj['class'] != 'person')
        
        # Check if we have an active detection for this camera
        if camera in self.active_detections:
            state = self.active_detections[camera]
            
            # Same person still there
            if state.person_name == person:
                # Check if objects changed significantly
                new_objects = current_objects - state.objects
                if new_objects:
                    # New objects appeared
                    state.objects = current_objects
                    state.last_seen = current_time
                    return True
                
                # Check cooldown
                time_since_last = (current_time - state.last_seen).total_seconds()
                if time_since_last > self.cooldown:
                    # Person been there long time, update timestamp
                    state.last_seen = current_time
                    return True  # Alert as "still here" reminder
                
                # Same person, same objects, within cooldown
                state.last_seen = current_time
                return False
            
            # Different person
            else:
                # Person changed
                state.person_name = person
                state.objects = current_objects
                state.last_seen = current_time
                state.alert_count += 1
                return True
        
        # New detection for this camera
        else:
            self.active_detections[camera] = DetectionState(
                person_name=person,
                objects=current_objects,
                last_seen=current_time,
                alert_count=1
            )
            return True
    
    def mark_left(self, camera: str):
        """Mark that person has left the camera view"""
        if camera in self.active_detections:
            del self.active_detections[camera]
    
    def get_scene_summary(self, camera: str) -> str:
        """Get summary of current scene for this camera"""
        if camera not in self.active_detections:
            return "Empty"
        
        state = self.active_detections[camera]
        objects_str = ", ".join(state.objects) if state.objects else "no objects"
        return f"{state.person_name} with {objects_str}"
    
    def cleanup_old(self, max_age_seconds: int = 600):
        """Remove detections older than max_age (assume person left)"""
        current_time = datetime.now()
        to_remove = []
        
        for camera, state in self.active_detections.items():
            age = (current_time - state.last_seen).total_seconds()
            if age > max_age_seconds:
                to_remove.append(camera)
        
        for camera in to_remove:
            del self.active_detections[camera]


class SmartAlertFilter:
    """
    High-level alert filtering combining multiple strategies
    """
    
    def __init__(self):
        self.deduplicator = AlertDeduplicator(cooldown_seconds=300)  # 5 min
        self.quality_filter = None  # Will be imported
        self.min_confidence = 0.6
        
    def process_detection(self, camera: str, person: str, objects: list, 
                         description: str, confidence: float) -> Optional[Dict]:
        """
        Process detection and decide if alert should be sent
        
        Returns:
            Alert dict if should alert, None otherwise
        """
        # Check confidence
        if confidence < self.min_confidence:
            return None
        
        # Check deduplication
        if not self.deduplicator.should_alert(camera, person, objects):
            return None
        
        # Build alert
        alert = {
            "camera": camera,
            "person": person,
            "objects": objects,
            "description": description,
            "confidence": confidence,
            "timestamp": datetime.now(),
            "is_new_detection": True
        }
        
        return alert
