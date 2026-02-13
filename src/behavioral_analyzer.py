"""Behavioral Analyzer Module - Track movement patterns and detect anomalies"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MovementEvent:
    """Represents a single movement detection event"""
    timestamp: datetime
    camera: str
    person_id: Optional[str]
    position: Tuple[float, float]  # x, y normalized coordinates (0-1)
    confidence: float
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "camera": self.camera,
            "person_id": self.person_id,
            "position": self.position,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MovementEvent":
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            camera=data["camera"],
            person_id=data.get("person_id"),
            position=tuple(data["position"]),
            confidence=data["confidence"]
        )


@dataclass
class BehavioralPattern:
    """Aggregated behavioral pattern for a person/zone/time"""
    person_id: Optional[str]
    camera: str
    hour_of_day: int
    day_of_week: int
    avg_duration_minutes: float
    frequency_score: float  # 0-1, how often this pattern occurs
    typical_positions: List[Tuple[float, float]]
    
    def to_dict(self) -> dict:
        return {
            "person_id": self.person_id,
            "camera": self.camera,
            "hour_of_day": self.hour_of_day,
            "day_of_week": self.day_of_week,
            "avg_duration_minutes": self.avg_duration_minutes,
            "frequency_score": self.frequency_score,
            "typical_positions": self.typical_positions
        }


class BehavioralAnalyzer:
    """
    Analyze behavioral patterns from movement data.
    
    Features:
    - Track person movement patterns across cameras/zones
    - Build time-series behavioral baseline
    - Detect anomalies in routines
    """
    
    def __init__(self, data_dir: Path, min_baseline_days: int = 7):
        self.data_dir = Path(data_dir)
        self.events_file = self.data_dir / "behavioral_events.jsonl"
        self.patterns_file = self.data_dir / "behavioral_patterns.json"
        self.min_baseline_days = min_baseline_days
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self.events: List[MovementEvent] = []
        self.patterns: Dict[str, BehavioralPattern] = {}
        
        # Anomaly detection threshold (percentile)
        self.anomaly_threshold = 0.95
        
        self._load_data()
        logger.info(f"BehavioralAnalyzer initialized with {len(self.events)} events")
    
    def _load_data(self):
        """Load existing events and patterns from disk"""
        # Load events
        if self.events_file.exists():
            try:
                with open(self.events_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            self.events.append(MovementEvent.from_dict(data))
                logger.info(f"Loaded {len(self.events)} behavioral events")
            except Exception as e:
                logger.error(f"Failed to load events: {e}")
        
        # Load patterns
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    for key, data in patterns_data.items():
                        self.patterns[key] = BehavioralPattern(**data)
                logger.info(f"Loaded {len(self.patterns)} behavioral patterns")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")
    
    def _save_event(self, event: MovementEvent):
        """Append event to persistent storage"""
        with open(self.events_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
    
    def _save_patterns(self):
        """Save patterns to persistent storage"""
        patterns_data = {k: asdict(v) for k, v in self.patterns.items()}
        with open(self.patterns_file, 'w') as f:
            json.dump(patterns_data, f, indent=2)
    
    def record_movement(self, camera: str, bbox: List[float], 
                       confidence: float, person_id: Optional[str] = None,
                       timestamp: Optional[datetime] = None) -> MovementEvent:
        """
        Record a movement event.
        
        Args:
            camera: Camera identifier
            bbox: Bounding box [x1, y1, x2, y2] in pixel coordinates
            confidence: Detection confidence
            person_id: Optional person identifier (for re-identification)
            timestamp: Event timestamp (defaults to now)
        
        Returns:
            Created MovementEvent
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Normalize bbox center to 0-1 range (assuming normalized coords)
        x_center = (bbox[0] + bbox[2]) / 2
        y_center = (bbox[1] + bbox[3]) / 2
        
        event = MovementEvent(
            timestamp=timestamp,
            camera=camera,
            person_id=person_id,
            position=(x_center, y_center),
            confidence=confidence
        )
        
        self.events.append(event)
        self._save_event(event)
        
        return event
    
    def build_baseline(self, days: Optional[int] = None) -> Dict:
        """
        Build behavioral baseline from collected events.
        
        Args:
            days: Number of days to analyze (None = all available)
        
        Returns:
            Summary statistics dict
        """
        if not self.events:
            logger.warning("No events to build baseline")
            return {}
        
        # Filter events by time window
        cutoff = datetime.now() - timedelta(days=days) if days else None
        events = [e for e in self.events if cutoff is None or e.timestamp >= cutoff]
        
        if not events:
            logger.warning("No events in specified time window")
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([
            {
                "timestamp": e.timestamp,
                "camera": e.camera,
                "person_id": e.person_id or "unknown",
                "hour": e.timestamp.hour,
                "day_of_week": e.timestamp.weekday(),
                "x": e.position[0],
                "y": e.position[1]
            }
            for e in events
        ])
        
        # Build patterns per camera/hour/day
        patterns = defaultdict(lambda: defaultdict(list))
        
        for _, row in df.iterrows():
            key = f"{row['camera']}_{row['hour']}_{row['day_of_week']}"
            patterns[key][row['person_id']].append({
                "timestamp": row['timestamp'],
                "position": (row['x'], row['y'])
            })
        
        # Create BehavioralPattern objects
        self.patterns = {}
        for key, person_data in patterns.items():
            camera, hour, dow = key.rsplit('_', 2)
            
            for person_id, occurrences in person_data.items():
                if len(occurrences) < 2:
                    continue
                
                # Calculate average duration
                timestamps = sorted([o['timestamp'] for o in occurrences])
                durations = []
                for i in range(1, len(timestamps)):
                    duration = (timestamps[i] - timestamps[i-1]).total_seconds() / 60
                    if duration < 30:  # Only count consecutive detections
                        durations.append(duration)
                
                avg_duration = np.mean(durations) if durations else 0
                
                # Calculate frequency score (normalized 0-1)
                total_days = (df['timestamp'].max() - df['timestamp'].min()).days or 1
                frequency = len(occurrences) / total_days
                frequency_score = min(frequency / 10, 1.0)  # Cap at 10 occurrences per day
                
                pattern_key = f"{person_id}_{camera}_{hour}_{dow}"
                self.patterns[pattern_key] = BehavioralPattern(
                    person_id=person_id if person_id != "unknown" else None,
                    camera=camera,
                    hour_of_day=int(hour),
                    day_of_week=int(dow),
                    avg_duration_minutes=float(avg_duration),
                    frequency_score=float(frequency_score),
                    typical_positions=[o['position'] for o in occurrences[:10]]
                )
        
        self._save_patterns()
        
        summary = {
            "total_events_analyzed": len(events),
            "patterns_created": len(self.patterns),
            "cameras": df['camera'].unique().tolist(),
            "date_range": {
                "start": df['timestamp'].min().isoformat(),
                "end": df['timestamp'].max().isoformat()
            },
            "most_active_hours": df.groupby('hour').size().nlargest(3).to_dict(),
            "most_active_cameras": df.groupby('camera').size().to_dict()
        }
        
        logger.info(f"Built baseline: {len(self.patterns)} patterns from {len(events)} events")
        return summary
    
    def detect_anomaly(self, event: MovementEvent) -> Optional[Dict]:
        """
        Detect if a movement event is anomalous.
        
        Args:
            event: Movement event to check
        
        Returns:
            Anomaly dict if anomalous, None otherwise
        """
        if not self.patterns:
            logger.warning("No baseline patterns available for anomaly detection")
            return None
        
        person_id = event.person_id or "unknown"
        key = f"{person_id}_{event.camera}_{event.timestamp.hour}_{event.timestamp.weekday()}"
        
        # Check if pattern exists
        if key not in self.patterns:
            # No baseline for this camera/hour/day combination
            # Check if person has ANY pattern
            person_patterns = [p for p in self.patterns.values() 
                             if p.person_id == event.person_id]
            
            if not person_patterns:
                return {
                    "type": "unknown_person",
                    "severity": "low",
                    "message": f"New person detected in {event.camera}",
                    "event": event.to_dict()
                }
            else:
                return {
                    "type": "unusual_time_location",
                    "severity": "medium",
                    "message": f"{person_id} in {event.camera} at unusual time",
                    "event": event.to_dict(),
                    "typical_locations": list(set(p.camera for p in person_patterns))
                }
        
        pattern = self.patterns[key]
        
        # Check if position is unusual
        event_pos = np.array(event.position)
        typical_positions = np.array(pattern.typical_positions)
        
        if len(typical_positions) > 0:
            distances = np.linalg.norm(typical_positions - event_pos, axis=1)
            min_distance = np.min(distances)
            
            # If position is far from typical positions
            if min_distance > 0.3:  # Threshold for significant position difference
                return {
                    "type": "unusual_position",
                    "severity": "low",
                    "message": f"Unusual position in {event.camera}",
                    "event": event.to_dict(),
                    "distance_from_typical": float(min_distance)
                }
        
        return None
    
    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """
        Get summary of activity for a specific day.
        
        Args:
            date: Date to summarize (defaults to today)
        
        Returns:
            Summary dict
        """
        if date is None:
            date = datetime.now()
        
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        day_events = [e for e in self.events 
                     if start <= e.timestamp < end]
        
        if not day_events:
            return {"message": "No activity recorded for this day"}
        
        df = pd.DataFrame([
            {"camera": e.camera, "hour": e.timestamp.hour, 
             "person_id": e.person_id or "unknown"}
            for e in day_events
        ])
        
        return {
            "date": start.strftime("%Y-%m-%d"),
            "total_events": len(day_events),
            "unique_cameras": df['camera'].unique().tolist(),
            "hourly_activity": df.groupby('hour').size().to_dict(),
            "camera_activity": df.groupby('camera').size().to_dict(),
            "persons_detected": df['person_id'].unique().tolist()
        }
    
    def has_sufficient_baseline(self) -> bool:
        """Check if we have enough data for anomaly detection"""
        if not self.events:
            return False
        
        date_range = self.events[-1].timestamp - self.events[0].timestamp
        return date_range.days >= self.min_baseline_days
    
    def export_for_training(self, output_path: Optional[Path] = None) -> Path:
        """
        Export behavioral data for model training.
        
        Args:
            output_path: Export destination
        
        Returns:
            Path to exported file
        """
        if output_path is None:
            output_path = self.data_dir / "behavioral_training_data.json"
        
        data = {
            "events": [e.to_dict() for e in self.events],
            "patterns": {k: asdict(v) for k, v in self.patterns.items()},
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "total_events": len(self.events),
                "total_patterns": len(self.patterns),
                "date_range": {
                    "start": self.events[0].timestamp.isoformat() if self.events else None,
                    "end": self.events[-1].timestamp.isoformat() if self.events else None
                }
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported behavioral data to {output_path}")
        return output_path


if __name__ == "__main__":
    # Test the behavioral analyzer
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = BehavioralAnalyzer(tmpdir, min_baseline_days=0)
        
        # Simulate some events
        now = datetime.now()
        for i in range(20):
            analyzer.record_movement(
                camera="sala" if i % 2 == 0 else "cozinha",
                bbox=[100, 100, 200, 300],
                confidence=0.85,
                person_id="person_1",
                timestamp=now - timedelta(hours=i)
            )
        
        # Build baseline
        summary = analyzer.build_baseline()
        print("Baseline summary:", json.dumps(summary, indent=2))
        
        # Check for anomalies
        test_event = MovementEvent(
            timestamp=now,
            camera="sala",
            person_id="person_1",
            position=(0.5, 0.5),
            confidence=0.9
        )
        
        anomaly = analyzer.detect_anomaly(test_event)
        print("Anomaly check:", anomaly)
        
        # Daily summary
        daily = analyzer.get_daily_summary()
        print("Daily summary:", json.dumps(daily, indent=2))
