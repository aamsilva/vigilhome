#!/usr/bin/env python3
"""Simple Test Monitor - Conservative settings"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from detector import ObjectDetector
from config import DATA_DIR

class SimpleTestMonitor:
    def __init__(self):
        self.detector = ObjectDetector()
        self.running = True
        self.last_alert = None
        self.alert_count = 0
        
    async def run_test(self, camera_name: str, duration_seconds: int = 120):
        """Run test for specified duration"""
        print(f"🧪 Teste iniciado: {camera_name}")
        print(f"⏱️ Duração: {duration_seconds}s")
        print(f"🚫 Cooldown: 60s entre alertas\n")
        
        start_time = datetime.now()
        last_alert_time = None
        
        while self.running:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > duration_seconds:
                print("\n✅ Teste concluído!")
                break
            
            try:
                # Get latest image
                image_dir = DATA_DIR / "highfreq" / datetime.now().strftime("%Y-%m-%d") / camera_name
                images = sorted(image_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)
                
                if images:
                    latest = images[0]
                    
                    # Detect
                    detections = self.detector.detect(latest)
                    people = [d for d in detections if d['class'] == 'person']
                    
                    if people:
                        current_time = datetime.now()
                        
                        # Check cooldown (60 seconds)
                        if last_alert_time:
                            time_since = (current_time - last_alert_time).total_seconds()
                            if time_since < 60:
                                print(f"   ⏳ Cooldown ativo ({int(60-time_since)}s restantes)")
                                await asyncio.sleep(5)
                                continue
                        
                        # Send alert
                        self.alert_count += 1
                        msg = f"🚶 TESTE #{self.alert_count}: Pessoa detetada na {camera_name} ({current_time.strftime('%H:%M:%S')})"
                        print(msg)
                        
                        # Send to Telegram
                        import subprocess
                        cmd = f'openclaw message send --target "-5291006422" --message "{msg}"'
                        subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
                        
                        last_alert_time = current_time
                        print(f"   ✅ Alerta enviado (próximo em 60s)\n")
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                await asyncio.sleep(10)
        
        print(f"\n📊 Total de alertas no teste: {self.alert_count}")
        print("🛑 Monitor parado")

if __name__ == "__main__":
    import sys
    camera = sys.argv[1] if len(sys.argv) > 1 else "cozinha"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    
    monitor = SimpleTestMonitor()
    try:
        asyncio.run(monitor.run_test(camera, duration))
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo utilizador")
        print(f"📊 Total de alertas: {monitor.alert_count}")
