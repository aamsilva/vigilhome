"""Smart Alert System - Text-only alerts with daily digest"""
import asyncio
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SmartAlertManager:
    """
    Smart alert system optimized for relevant notifications only
    
    Features:
    - Text-only real-time alerts (no images)
    - Alert only on significant changes
    - Daily digest with images for training
    - Quiet hours (23:00-07:00)
    """
    
    def __init__(self, config_path: Path, telegram_notifier):
        self.config = self._load_config(config_path)
        self.notifier = telegram_notifier
        self.last_alerts = {}  # Track last alert per person/location
        self.active_persons = {}  # Track who is currently where
        self.daily_images = []  # Collect images for daily digest
        
    def _load_config(self, path: Path) -> Dict:
        with open(path) as f:
            return yaml.safe_load(f)
    
    async def process_detection(self, camera: str, person: str, 
                               objects: list, description: str, 
                               confidence: float, image_path: Path) -> Optional[str]:
        """
        Process detection and decide if alert should be sent
        
        Returns:
            Alert message if should alert, None otherwise
        """
        # Check quiet hours
        if self._is_quiet_hours() and not self._is_emergency(person, description):
            return None
        
        # Check if new person arrived
        if self._is_new_person(camera, person):
            msg = self._format_new_person_alert(camera, person)
            self._track_person(camera, person)
            await self._send_text_alert(msg)
            return msg
        
        # Check if person left
        if self._has_person_left(camera, person):
            msg = self._format_person_left_alert(camera, person)
            self._remove_person(camera, person)
            await self._send_text_alert(msg)
            return msg
        
        # Check for unknown person
        if person == "unknown" or person == "desconhecido":
            if self._should_alert_unknown():
                msg = f"⚠️ Pessoa desconhecida na {camera} ({self._now()})"
                await self._send_text_alert(msg)
                return msg
        
        # Store image for daily digest (if interesting)
        if self._is_interesting_for_training(camera, person, objects):
            self.daily_images.append({
                'path': image_path,
                'camera': camera,
                'person': person,
                'description': description,
                'time': datetime.now()
            })
        
        return None
    
    def _is_new_person(self, camera: str, person: str) -> bool:
        """Check if this person just arrived at this camera"""
        key = f"{camera}:{person}"
        
        # Not currently tracked at this location
        if key not in self.active_persons:
            # Check cooldown (don't alert if was here recently)
            last_seen = self.last_alerts.get(key)
            if last_seen:
                time_since = (datetime.now() - last_seen).total_seconds()
                cooldown = self.config.get('smart_filtering', {}).get('min_time_between_alerts', 300)
                if time_since < cooldown:
                    return False
            return True
        
        return False
    
    def _has_person_left(self, camera: str, person: str) -> bool:
        """Check if person was here but now left"""
        key = f"{camera}:{person}"
        
        if key in self.active_persons:
            # Check if been absent for a while
            last_seen = self.active_persons[key]
            time_absent = (datetime.now() - last_seen).total_seconds()
            
            # If not seen for 2 minutes, consider left
            if time_absent > 120:
                return True
        
        return False
    
    def _track_person(self, camera: str, person: str):
        """Track person as active at location"""
        key = f"{camera}:{person}"
        self.active_persons[key] = datetime.now()
        self.last_alerts[key] = datetime.now()
    
    def _remove_person(self, camera: str, person: str):
        """Remove person from active tracking"""
        key = f"{camera}:{person}"
        if key in self.active_persons:
            del self.active_persons[key]
    
    def _should_alert_unknown(self) -> bool:
        """Check if should alert about unknown person"""
        last_unknown = self.last_alerts.get('unknown', datetime.min)
        time_since = (datetime.now() - last_unknown).total_seconds()
        return time_since > 300  # Max 1 alert per 5 min
    
    def _is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours"""
        quiet = self.config.get('quiet_hours', {})
        if not quiet.get('enabled', False):
            return False
        
        now = datetime.now()
        start = datetime.strptime(quiet['start'], "%H:%M").time()
        end = datetime.strptime(quiet['end'], "%H:%M").time()
        
        current_time = now.time()
        
        if start < end:
            return start <= current_time <= end
        else:  # Crosses midnight
            return current_time >= start or current_time <= end
    
    def _is_emergency(self, person: str, description: str) -> bool:
        """Check if this is an emergency alert that should bypass quiet hours"""
        emergencies = ['unknown', 'intrusion', 'break', 'glass', 'anomaly']
        desc_lower = description.lower()
        return any(e in desc_lower for e in emergencies)
    
    def _format_new_person_alert(self, camera: str, person: str) -> str:
        """Format alert for new person arrival"""
        emoji = "🚶" if person in ['augusto', 'sofia', 'maria_rita'] else "👤"
        return f"{emoji} {person.capitalize()} chegou à {camera} ({self._now()})"
    
    def _format_person_left_alert(self, camera: str, person: str) -> str:
        """Format alert for person leaving"""
        return f"👋 {person.capitalize()} saiu de {camera} ({self._now()})"
    
    async def _send_text_alert(self, message: str):
        """Send text-only alert via Telegram"""
        try:
            # Import here to avoid circular dependency
            from message import message as msg_tool
            await msg_tool(action="send", target="-5291006422", message=message)
            logger.info(f"Alert sent: {message}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def _is_interesting_for_training(self, camera: str, person: str, objects: list) -> bool:
        """Check if this image is worth saving for daily digest"""
        # Limit daily images
        if len(self.daily_images) >= 20:
            return False
        
        # Save if:
        # - Different person than usual
        # - Different camera than usual for this person
        # - Contains interesting objects
        
        return True  # For now, save all
    
    async def send_daily_digest(self):
        """Send daily summary with images for training"""
        if not self.daily_images:
            return
        
        # Select best 10 images
        selected = self.daily_images[:10]
        
        # Send summary message
        summary = f"""📸 Imagens do dia para treino - {datetime.now().strftime('%Y-%m-%d')}

Por favor identifica:
"""
        for i, img in enumerate(selected, 1):
            summary += f"\n{i}. Câmara {img['camera']} às {img['time'].strftime('%H:%M')}"
            if img['person'] != 'unknown':
                summary += f" - Parece ser: {img['person']}"
        
        summary += "\n\nObrigado por ajudar a melhorar! 🤖"
        
        await self._send_text_alert(summary)
        
        # Send images one by one
        for img in selected:
            try:
                from message import message as msg_tool
                await msg_tool(
                    action="send", 
                    target="-5291006422",
                    media=str(img['path']),
                    caption=f"{img['camera']} - {img['time'].strftime('%H:%M')}"
                )
            except Exception as e:
                logger.error(f"Failed to send image: {e}")
        
        # Clear daily images
        self.daily_images = []
    
    def _now(self) -> str:
        return datetime.now().strftime("%H:%M")
    
    def cleanup_old_tracking(self):
        """Remove old entries from tracking"""
        now = datetime.now()
        to_remove = []
        
        for key, last_seen in self.active_persons.items():
            if (now - last_seen).total_seconds() > 600:  # 10 minutes
                to_remove.append(key)
        
        for key in to_remove:
            del self.active_persons[key]


# Test
if __name__ == "__main__":
    print("Smart Alert System loaded")
