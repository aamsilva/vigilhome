"""Daily Presence Report - Track family members' presence and activities"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PresenceEvent:
    timestamp: datetime
    person: str
    camera: str
    event_type: str  # 'entered', 'exited', 'seen'
    confidence: float

class DailyPresenceReport:
    """Generate daily reports of family presence and activities"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.reports_dir = data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict:
        """Generate report for a specific day"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        
        # Load detections for the day
        detections_file = self.data_dir / "logs" / f"detections_{date_str}.jsonl"
        
        family_presence = {
            "augusto": {"first_seen": None, "last_seen": None, "total_time": 0, "cameras": set()},
            "sofia": {"first_seen": None, "last_seen": None, "total_time": 0, "cameras": set()},
            "maria_rita": {"first_seen": None, "last_seen": None, "total_time": 0, "cameras": set()},
        }
        
        # Process detections
        if detections_file.exists():
            with open(detections_file) as f:
                for line in f:
                    try:
                        detection = json.loads(line)
                        person = detection.get("person", "unknown")
                        if person in family_presence:
                            ts = datetime.fromisoformat(detection["timestamp"])
                            cam = detection["camera"]
                            
                            if family_presence[person]["first_seen"] is None:
                                family_presence[person]["first_seen"] = ts
                            family_presence[person]["last_seen"] = ts
                            family_presence[person]["cameras"].add(cam)
                    except:
                        continue
        
        # Calculate time spent
        for person, data in family_presence.items():
            if data["first_seen"] and data["last_seen"]:
                duration = (data["last_seen"] - data["first_seen"]).total_seconds() / 3600
                data["total_time"] = round(duration, 2)
            data["cameras"] = list(data["cameras"])
        
        report = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_detections": 0,
                "people_at_home": [p for p, d in family_presence.items() if d["first_seen"]]
            },
            "family_members": family_presence
        }
        
        return report
    
    def format_report_telegram(self, report: Dict) -> str:
        """Format report for Telegram message"""
        date = report["date"]
        msg = f"📊 **Relatório Diário - {date}**\n\n"
        
        for person, data in report["family_members"].items():
            if data["first_seen"]:
                name = person.capitalize()
                first = data["first_seen"].strftime("%H:%M") if data["first_seen"] else "N/A"
                last = data["last_seen"].strftime("%H:%M") if data["last_seen"] else "N/A"
                hours = data["total_time"]
                
                msg += f"👤 **{name}**\n"
                msg += f"   🕐 Chegada: {first}\n"
                msg += f"   🕐 Saída: {last}\n"
                msg += f"   ⏱️ Tempo em casa: ~{hours}h\n"
                msg += f"   📍 Câmaras: {', '.join(data['cameras'])}\n\n"
            else:
                msg += f"👤 **{person.capitalize()}**: Não detetado\n\n"
        
        return msg
    
    def save_report(self, report: Dict):
        """Save report to file"""
        date = report["date"]
        report_file = self.reports_dir / f"presence_{date}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)


class DoorExitDetector:
    """Detect when someone exits/enters through a door"""
    
    def __init__(self):
        self.door_zones = {
            "cozinha": ["porta"],  # door zone in cozinha
            "sala": ["entrada"]    # entrance zone in sala
        }
        self.recent_movements = []
    
    def detect_exit(self, camera: str, zone: str, direction: str) -> Optional[str]:
        """
        Detect if someone is exiting or entering
        
        Returns:
            'exit', 'enter', or None
        """
        # Simple heuristic: if moving toward door zone and then disappears
        # This would need tracking across multiple frames
        pass
    
    def track_movement(self, person_bbox, camera, timestamp):
        """Track movement toward/away from door"""
        pass
