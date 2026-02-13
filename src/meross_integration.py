"""Meross Integration - Control blinds/shutters via Meross API"""
import os
import json
import asyncio
from typing import Dict, List, Optional
from pathlib import Path

class MerossController:
    """Control Meross devices (blinds, lights, etc.)"""
    
    def __init__(self, email: str = None, password: str = None):
        self.email = email or os.getenv("MEROSS_EMAIL")
        self.password = password or os.getenv("MEROSS_PASSWORD")
        self.manager = None
        self.devices = {}
    
    async def connect(self):
        """Connect to Meross cloud and discover devices"""
        try:
            from meross_iot.http_api import MerossHttpClient
            from meross_iot.manager import MerossManager
            
            # Login
            http_api_client = await MerossHttpClient.async_from_user_password(
                api_base_url="https://iot.meross.com",
                email=self.email,
                password=self.password
            )
            
            # Create manager
            self.manager = MerossManager(http_client=http_api_client)
            await self.manager.async_init()
            
            # Discover devices
            await self.manager.async_device_discovery()
            self.devices = self.manager.find_devices()
            
            print(f"Connected! Found {len(self.devices)} devices")
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def list_blinds(self) -> List[Dict]:
        """List all roller shutter/blind devices"""
        blinds = []
        for device in self.devices:
            if hasattr(device, 'name'):
                device_info = {
                    "name": device.name,
                    "type": type(device).__name__,
                    "online": device.online_status.name if hasattr(device, 'online_status') else "unknown"
                }
                blinds.append(device_info)
        return blinds
    
    async def open_blind(self, device_name: str):
        """Open a specific blind"""
        for device in self.devices:
            if device.name == device_name and hasattr(device, 'async_open'):
                await device.async_open(channel=0)
                print(f"Opening {device_name}")
                return True
        return False
    
    async def close_blind(self, device_name: str):
        """Close a specific blind"""
        for device in self.devices:
            if device.name == device_name and hasattr(device, 'async_close'):
                await device.async_close(channel=0)
                print(f"Closing {device_name}")
                return True
        return False
    
    async def stop_blind(self, device_name: str):
        """Stop a blind in current position"""
        for device in self.devices:
            if device.name == device_name and hasattr(device, 'async_stop'):
                await device.async_stop(channel=0)
                print(f"Stopping {device_name}")
                return True
        return False
    
    async def get_status(self, device_name: str) -> Optional[str]:
        """Get current status of a blind"""
        for device in self.devices:
            if device.name == device_name:
                if hasattr(device, 'get_current_position'):
                    pos = await device.async_get_current_position(channel=0)
                    return f"Position: {pos}%"
                return "Status available"
        return None
    
    async def disconnect(self):
        """Disconnect from Meross cloud"""
        if self.manager:
            self.manager.close()
            print("Disconnected from Meross")


# Smart home automation rules
def should_close_blinds(person_detected: bool, time_of_day: str, privacy_mode: bool = False) -> bool:
    """
    Decide if blinds should close based on context
    
    Returns True if blinds should close
    """
    # Privacy mode: close when person detected
    if privacy_mode and person_detected:
        return True
    
    # Night mode: close after sunset
    if time_of_day == "night":
        return True
    
    # Cinema mode: close when watching TV (person + TV on)
    if person_detected:
        return False  # Keep open during day
    
    return False


# Integration with VigilHome
class VigilHomeBlindsIntegration:
    """Integrate Meross blinds with VigilHome surveillance"""
    
    def __init__(self, meross_controller: MerossController):
        self.meross = meross_controller
        self.room_mapping = {
            "sala": ["Estores Sala", "Blinds Living Room"],
            "cozinha": ["Estores Cozinha", "Blinds Kitchen"],
            "quarto": ["Estores Quarto", "Blinds Bedroom"]
        }
    
    async def privacy_mode(self, camera: str, person_detected: bool):
        """Close blinds for privacy when person detected"""
        if not person_detected:
            return
        
        # Map camera to room
        room = self._get_room_from_camera(camera)
        if room:
            blinds = self.room_mapping.get(room, [])
            for blind_name in blinds:
                await self.meross.close_blind(blind_name)
                print(f"Privacy mode: Closed {blind_name}")
    
    def _get_room_from_camera(self, camera: str) -> Optional[str]:
        """Map camera name to room"""
        mapping = {
            "sala": "sala",
            "cozinha": "cozinha"
        }
        return mapping.get(camera)
    
    async def handle_command(self, command: str, room: str = None):
        """Handle voice/chat commands"""
        command = command.lower()
        
        if "fecha" in command or "close" in command:
            if room:
                blinds = self.room_mapping.get(room, [])
                for blind in blinds:
                    await self.meross.close_blind(blind)
            else:
                # Close all
                for room_blinds in self.room_mapping.values():
                    for blind in room_blinds:
                        await self.meross.close_blind(blind)
                        
        elif "abre" in command or "open" in command:
            if room:
                blinds = self.room_mapping.get(room, [])
                for blind in blinds:
                    await self.meross.open_blind(blind)
            else:
                # Open all
                for room_blinds in self.room_mapping.values():
                    for blind in room_blinds:
                        await self.meross.open_blind(blind)


# Test function
async def test_meross_connection():
    """Test Meross connection and list devices"""
    import os
    
    email = os.getenv("MEROSS_EMAIL")
    password = os.getenv("MEROSS_PASSWORD")
    
    if not email or not password:
        print("Meross credentials not found in environment")
        return
    
    controller = MerossController(email, password)
    
    try:
        connected = await controller.connect()
        if connected:
            blinds = controller.list_blinds()
            print(f"\nFound {len(blinds)} devices:")
            for blind in blinds:
                print(f"  - {blind['name']} ({blind['type']}) - {blind['online']}")
        else:
            print("Failed to connect to Meross")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await controller.disconnect()


if __name__ == "__main__":
    # Run test
    asyncio.run(test_meross_connection())
