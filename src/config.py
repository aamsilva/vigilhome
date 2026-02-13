"""VigilHome Configuration"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path("/Users/augustosilva/clawd/projects/video-surveillance-rnd")
DATA_DIR = Path("/Volumes/disco1tb/video-surv")
MODELS_DIR = BASE_DIR / "models"

# Camera Configuration
CAMERAS = {
    "sala": {
        "ip": "192.168.86.23",
        "location": "Sala de estar",
        "zones": ["entrada", "sofa", "janela"]
    },
    "cozinha": {
        "ip": "192.168.86.51",
        "location": "Cozinha",
        "zones": ["porta", "balcao", "mesa"]
    },
    "exterior": {
        "ip": "192.168.86.78",
        "location": "Exterior",
        "zones": ["entrada", "jardim", "portao"],
        "status": "pending"  # Not responding yet
    }
}

# Capture Configuration
CAPTURE_CONFIG = {
    "highfreq_dir": DATA_DIR / "highfreq",
    "archive_dir": DATA_DIR / "captures",
    "interval_seconds": 30,
    "retention_days": 30
}

# AI Model Configuration
MODEL_CONFIG = {
    # YOLO for object detection
    "yolo": {
        "model": "yolo11n.pt",  # nano = fastest
        "conf_threshold": 0.5,
        "classes": ["person", "dog", "cat", "backpack", "handbag", "suitcase", 
                   "bottle", "cup", "laptop", "cell phone", "book"]
    },
    # VLM for scene understanding
    "vlm": {
        "model": "minicpm-v-2_6",  # Will download quantized version
        "context_length": 4096,
        "temperature": 0.7
    },
    # Embedding model for semantic search
    "embeddings": {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": 384
    }
}

# Vector Database
CHROMA_CONFIG = {
    "persist_directory": str(DATA_DIR / "chroma_db"),
    "collection_name": "vigilhome_events"
}

# Feature Flags
FEATURES = {
    "scene_understanding": True,   # Feature 1
    "behavioral_baseline": True,   # Feature 2
    "semantic_search": True,       # Feature 6
    "person_reid": False,          # Feature 5 (future)
    "fall_detection": False        # Feature 7 (future)
}

# Telegram Configuration (for alerts)
TELEGRAM_CONFIG = {
    "chat_id": "-5291006422",
    "send_descriptions": True,
    "send_anomalies": True
}

# Logging
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": DATA_DIR / "logs" / "vigilhome.log"
}
