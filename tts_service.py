"""
Service for text-to-speech conversion using HuggingFace models.
"""

import os
import logging
import tempfile
from typing import Optional
import torch
from transformers import AutoModelForTextToWaveform, AutoTokenizer

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.thai_model = None
        self.thai_tokenizer = None
        self.russian_model = None
        self.russian_tokenizer = None
        self.models_loaded = False
        
    def initialize_models(self) -> bool:
        """Initialize all TTS models"""
        logger.info("Initializing TTS models...")
        
        try:
            # Load Thai model
            logger.info("Loading Thai TTS model...")
            self.thai_model = AutoModelForTextToWaveform.from_pretrained("facebook/mms-tts-tha")
            self.thai_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tha")
            logger.info("Thai TTS model loaded successfully")
            
            # Load Russian model
            logger.info("Loading Russian TTS model...")
            self.russian_model = AutoModelForTextToWaveform.from_pretrained("facebook/mms-tts-rus")
            self.russian_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-rus")
            logger.info("Russian TTS model loaded successfully")
            
            self.models_loaded = True
            logger.info("All TTS models initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS models: {e}")
            self.models_loaded = False
            return False
            
    def _ensure_models_loaded(self) -> bool:
        """Ensure models are loaded"""
        if not self.models_loaded:
            return self.initialize_models()
        return True
    
    def text_to_speech(self, text: str, lang: str) -> Optional[str]:
        """Convert text to speech using appropriate model"""
        try:
            # Ensure models are loaded
            if not self._ensure_models_loaded():
                logger.error("TTS models not loaded")
                return None
                
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            if lang == 'th':
                # Generate audio using Thai model
                inputs = self.thai_tokenizer(text, return_tensors="pt")
                with torch.no_grad():
                    output = self.thai_model(**inputs)
                
                # Save audio
                import soundfile as sf
                sf.write(temp_path, output.waveform.numpy().squeeze(), self.thai_model.config.sampling_rate)
                
            elif lang == 'ru':
                # Generate audio using Russian model
                inputs = self.russian_tokenizer(text, return_tensors="pt")
                with torch.no_grad():
                    output = self.russian_model(**inputs)
                
                # Save audio
                import soundfile as sf
                sf.write(temp_path, output.waveform.numpy().squeeze(), self.russian_model.config.sampling_rate)
                
            else:
                logger.error(f"Unsupported language for TTS: {lang}")
                return None
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None