"""Automation Engine - Execute smart home automations"""
import asyncio
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AutomationEngine:
    """Execute automations based on triggers"""
    
    def __init__(self, config_path: Path, meross_controller):
        self.config = self._load_config(config_path)
        self.meross = meross_controller
        self.running = False
        self.last_states = {}
        
    def _load_config(self, path: Path) -> Dict:
        """Load automation config from YAML"""
        with open(path) as f:
            return yaml.safe_load(f)
    
    async def start(self):
        """Start automation engine"""
        self.running = True
        logger.info("Automation engine started")
        
        while self.running:
            await self._check_time_based_automations()
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_time_based_automations(self):
        """Check and execute time-based automations"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        for name, auto in self.config.get("automations", {}).items():
            if not auto.get("enabled", False):
                continue
                
            for trigger in auto.get("triggers", []):
                if trigger.get("type") == "time":
                    if trigger.get("time") == current_time:
                        await self._execute_automation(name, auto)
    
    async def _execute_automation(self, name: str, automation: Dict):
        """Execute automation actions"""
        logger.info(f"Executing automation: {name}")
        
        for action in automation.get("actions", []):
            action_type = action.get("action")
            exclude = action.get("exclude", [])
            
            if action_type == "close_all_blinds":
                await self._close_all_blinds(exclude)
            elif action_type == "open_all_blinds":
                await self._open_all_blinds(exclude)
            elif action_type == "close_blinds":
                rooms = action.get("rooms", [])
                await self._close_blinds_by_room(rooms, exclude)
            elif action_type == "open_blinds":
                rooms = action.get("rooms", [])
                await self._open_blinds_by_room(rooms, exclude)
    
    async def _close_all_blinds(self, exclude: List[str]):
        """Close all blinds except excluded"""
        blinds = self._get_available_blinds(exclude)
        for blind in blinds:
            try:
                await self.meross.close_blind(blind)
                await asyncio.sleep(2)  # Safety delay
            except Exception as e:
                logger.error(f"Failed to close {blind}: {e}")
    
    async def _open_all_blinds(self, exclude: List[str]):
        """Open all blinds except excluded"""
        blinds = self._get_available_blinds(exclude)
        for blind in blinds:
            try:
                await self.meross.open_blind(blind)
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Failed to open {blind}: {e}")
    
    def _get_available_blinds(self, exclude: List[str]) -> List[str]:
        """Get list of available blinds excluding broken ones"""
        all_blinds = [
            "estore_sala_tv",
            "estore_sala_varanda",
            "estore_quarto_pais",
            "estore_quarto_rita",
            "estore_escritorio",
            "estorr_vicente"
        ]
        return [b for b in all_blinds if b not in exclude]
    
    def stop(self):
        """Stop automation engine"""
        self.running = False
        logger.info("Automation engine stopped")
    
    # Event handlers for detection-based automations
    async def on_person_detected(self, camera: str, person: str):
        """Handle person detection event"""
        # Check privacy mode
        privacy = self.config.get("automations", {}).get("privacy_mode", {})
        if privacy.get("enabled") and camera in ["sala", "cozinha"]:
            # Check time exception
            now = datetime.now()
            if not (8 <= now.hour < 18):  # Outside daytime
                await self._execute_automation("privacy_mode", privacy)
    
    async def handle_telegram_command(self, command: str) -> str:
        """Handle Telegram command for blinds"""
        commands = self.config.get("commands", [])
        
        for cmd in commands:
            if cmd.get("name") in command.lower():
                # Execute command
                action = cmd.get("action")
                exclude = cmd.get("exclude", [])
                rooms = cmd.get("rooms", [])
                
                if action == "close_all_blinds":
                    await self._close_all_blinds(exclude)
                    return "✅ Todos os estores fechados (exceto cozinha)"
                elif action == "open_all_blinds":
                    await self._open_all_blinds(exclude)
                    return "✅ Todos os estores abertos (exceto cozinha)"
                elif action == "close_blinds" and rooms:
                    await self._close_blinds_by_room(rooms, exclude)
                    return f"✅ Estores fechados: {', '.join(rooms)}"
                elif action == "open_blinds" and rooms:
                    await self._open_blinds_by_room(rooms, exclude)
                    return f"✅ Estores abertos: {', '.join(rooms)}"
        
        return "❌ Comando não reconhecido"
    
    async def _close_blinds_by_room(self, rooms: List[str], exclude: List[str]):
        """Close blinds by room name"""
        room_mapping = {
            "sala": ["estore_sala_tv", "estore_sala_varanda"],
            "quarto_pais": ["estore_quarto_pais"],
            "quarto_rita": ["estore_quarto_rita"],
            "escritorio": ["estore_escritorio"]
        }
        
        for room in rooms:
            blinds = room_mapping.get(room, [])
            for blind in blinds:
                if blind not in exclude:
                    try:
                        await self.meross.close_blind(blind)
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"Failed to close {blind}: {e}")
    
    async def _open_blinds_by_room(self, rooms: List[str], exclude: List[str]):
        """Open blinds by room name"""
        room_mapping = {
            "sala": ["estore_sala_tv", "estore_sala_varanda"],
            "quarto_pais": ["estore_quarto_pais"],
            "quarto_rita": ["estore_quarto_rita"],
            "escritorio": ["estore_escritorio"]
        }
        
        for room in rooms:
            blinds = room_mapping.get(room, [])
            for blind in blinds:
                if blind not in exclude:
                    try:
                        await self.meross.open_blind(blind)
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"Failed to open {blind}: {e}")


# Simple test
if __name__ == "__main__":
    print("Automation engine loaded")
    print("Available automations:")
    config = AutomationEngine._load_config(None, Path("../config/automations.yaml"))
    for name, auto in config.get("automations", {}).items():
        print(f"  - {name}: {auto.get('description', 'No description')}")
