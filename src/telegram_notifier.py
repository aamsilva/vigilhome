"""Telegram Notifier for VigilHome Alerts"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Send surveillance alerts to Telegram"""
    
    def __init__(self, chat_id: str = "-5291006422"):
        self.chat_id = chat_id
        self.enabled = True
    
    def send_detection(self, camera: str, image_path: Path, description: str, person_count: int = 0):
        """Send person detection alert"""
        if not self.enabled:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if person_count > 0:
            emoji = "🚶" if person_count == 1 else "👥"
            msg = f"{emoji} *Pessoa detetada*\n\n"
            msg += f"📍 Câmara: `{camera}`\n"
            msg += f"🕐 Hora: `{timestamp}`\n"
            msg += f"👥 Count: `{person_count}`\n"
            if description:
                msg += f"\n📝 {description}"
        else:
            return  # Don't spam for empty detections
        
        self._send_message(msg, image_path)
    
    def send_anomaly(self, camera: str, anomaly_type: str, details: str, severity: str = "medium"):
        """Send behavioral anomaly alert"""
        if not self.enabled:
            return
        
        emojis = {
            "high": "🚨",
            "medium": "⚠️",
            "low": "ℹ️"
        }
        
        emoji = emojis.get(severity, "⚠️")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        msg = f"{emoji} *Anomalia Comportamental*\n\n"
        msg += f"📍 Câmara: `{camera}`\n"
        msg += f"🕐 Hora: `{timestamp}`\n"
        msg += f"⚡ Tipo: `{anomaly_type}`\n"
        msg += f"📝 {details}"
        
        self._send_message(msg)
    
    def send_daily_summary(self, stats: Dict[str, Any]):
        """Send daily activity summary"""
        if not self.enabled:
            return
        
        msg = "📊 *Resumo Diário - VigilHome*\n\n"
        msg += f"📸 Total de capturas: `{stats.get('total_captures', 0)}`\n"
        msg += f"🚶 Pessoas detetadas: `{stats.get('person_detections', 0)}`\n"
        msg += f"⚠️ Anomalias: `{stats.get('anomalies', 0)}`\n"
        msg += f"🔍 Eventos indexados: `{stats.get('indexed_events', 0)}`\n\n"
        msg += "_Sistema operacional_ ✅"
        
        self._send_message(msg)
    
    def _send_message(self, text: str, image_path: Optional[Path] = None):
        """Send message via Telegram (using OpenClaw message tool)"""
        try:
            # Log for now - actual sending happens through OpenClaw
            logger.info(f"Telegram alert: {text[:100]}...")
            
            # In production, this would call:
            # message(action="send", target=self.chat_id, message=text, media=str(image_path) if image_path else None)
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
    
    def send_test(self):
        """Send test message"""
        msg = "🤖 *VigilHome Alert System*\n\n"
        msg += "✅ Notificações ativadas neste grupo!\n\n"
        msg += "Tipos de alertas configurados:\n"
        msg += "• 🚶 Deteção de pessoas\n"
        msg += "• ⚠️ Anomalias comportamentais\n"
        msg += "• 📝 Resumos diários\n"
        msg += "• 🔍 Eventos de segurança\n\n"
        msg += "_Sistema pronto para enviar alertas automáticos._"
        
        self._send_message(msg)
        return msg


if __name__ == "__main__":
    # Test
    notifier = TelegramNotifier()
    notifier.send_test()
    print("Test message prepared")
