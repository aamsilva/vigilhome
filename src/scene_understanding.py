"""Scene Understanding Module - VLM for natural language descriptions"""
import logging
from pathlib import Path
from typing import Optional
import base64
import torch

logger = logging.getLogger(__name__)

class SceneUnderstanding:
    """Generate natural language descriptions of surveillance scenes"""
    
    def __init__(self, model_name: str = "minicpm-v"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self._load_model()
    
    def _load_model(self):
        """Load vision-language model"""
        try:
            # Use BLIP for image captioning
            from transformers import BlipProcessor, BlipForConditionalGeneration
            from PIL import Image
            
            self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            
            # Move to MPS if available (Apple Silicon)
            try:
                import torch
                if torch.backends.mps.is_available():
                    self.model = self.model.to("mps")
                    logger.info("Model moved to MPS (Apple Silicon)")
                else:
                    logger.info("Running on CPU")
            except:
                pass
                
            logger.info("Loaded BLIP image captioning model")
        except Exception as e:
            logger.error(f"Failed to load VLM: {e}")
            self.model = None
            self.processor = None
    
    def describe_scene(self, image_path: Path, context: Optional[dict] = None) -> str:
        """
        Generate natural language description of scene
        
        Args:
            image_path: Path to image file
            context: Optional context (camera name, time, previous detections)
        
        Returns:
            Natural language description
        """
        if not self.model or not self.processor:
            return "Scene understanding not available"
        
        try:
            from PIL import Image
            
            # Load and process image
            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(image, return_tensors="pt")
            
            # Move inputs to same device as model
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                output = self.model.generate(**inputs, max_new_tokens=50)
            
            description = self.processor.decode(output[0], skip_special_tokens=True)
            
            # Enhance with context if available
            if context:
                camera = context.get("camera", "Unknown")
                time = context.get("time", "")
                description = f"[{camera}] {description}"
            
            return description
        except Exception as e:
            logger.error(f"Scene description failed: {e}")
            return "Error analyzing scene"
    
    def describe_with_objects(self, image_path: Path, detections: list) -> str:
        """
        Generate description incorporating object detections
        
        Args:
            image_path: Path to image
            detections: List of detection dicts from ObjectDetector
        
        Returns:
            Rich description with objects
        """
        base_desc = self.describe_scene(image_path)
        
        # Add object information
        object_counts = {}
        for det in detections:
            cls = det["class"]
            object_counts[cls] = object_counts.get(cls, 0) + 1
        
        if object_counts:
            objects_str = ", ".join([f"{n} {c}" for c, n in object_counts.items()])
            return f"{base_desc}. Detected: {objects_str}."
        
        return base_desc


if __name__ == "__main__":
    # Test
    su = SceneUnderstanding()
    test_image = Path("/Volumes/disco1tb/video-surv/highfreq/2026-02-13/sala/190000.jpg")
    if test_image.exists():
        desc = su.describe_scene(test_image, {"camera": "sala", "time": "19:00"})
        print(f"Description: {desc}")
