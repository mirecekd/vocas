"""
TTS služby pro Vocas 2.0
"""
import os
import uuid
import logging
from typing import Optional

from .base import BaseTTS
from .edge_tts_provider import EdgeTTS
from .elevenlabs_tts_provider import ElevenLabsTTS
from .polly_tts_provider import PollyTTS

logger = logging.getLogger(__name__)

class TTSService:
    """
    Hlavní TTS služba podporující více providerů.
    """
    
    def __init__(self, output_dir: str = "static/audio", provider: str = "edge"):
        """
        Inicializace TTS služby.
        
        Args:
            output_dir: Výstupní složka pro audio soubory
            provider: TTS provider ('edge', 'elevenlabs', 'polly')
        """
        self.output_dir = output_dir
        self.provider_name = provider
        os.makedirs(output_dir, exist_ok=True)
        
        # Inicializace providera
        self.provider = self._init_provider(provider)
        
        if self.provider:
            logger.info(f"TTS Service initialized with: {self.provider.get_provider_name()}")
        else:
            logger.error(f"Failed to initialize TTS provider: {provider}")
    
    def _init_provider(self, provider: str):
        """
        Inicializuje TTS providera podle názvu.
        
        Args:
            provider: Název providera
            
        Returns:
            Instance TTS providera nebo None
        """
        try:
            if provider == "edge":
                # Edge TTS - zdarma, dobré české hlasy
                return EdgeTTS(
                    voice=os.getenv('EDGE_VOICE', 'cs-CZ-AntoninNeural'),
                    rate=os.getenv('EDGE_RATE', '+0%'),
                    pitch=os.getenv('EDGE_PITCH', '+0Hz')
                )
            
            elif provider == "elevenlabs":
                # ElevenLabs - vyžaduje API klíč
                api_key = os.getenv('ELEVENLABS_API_KEY')
                voice_id = os.getenv('ELEVENLABS_VOICE_ID')
                
                if not api_key or not voice_id:
                    logger.error("ElevenLabs credentials not found in environment")
                    return None
                
                return ElevenLabsTTS(
                    api_key=api_key,
                    voice_id=voice_id,
                    model_id=os.getenv('ELEVENLABS_MODEL_ID', 'eleven_multilingual_v2')
                )
            
            elif provider == "polly":
                # AWS Polly - vyžaduje AWS credentials
                if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
                    logger.error("AWS credentials not found in environment")
                    return None
                
                return PollyTTS(
                    voice_id=os.getenv('POLLY_VOICE_ID', 'Iveta'),
                    region=os.getenv('AWS_REGION', 'eu-central-1')
                )
            
            else:
                logger.error(f"Unknown TTS provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error initializing TTS provider {provider}: {e}")
            return None
    
    def generate_audio(self, text: str) -> Optional[str]:
        """
        Generuje MP3 audio z textu.
        
        Args:
            text: Text k přečtení
            
        Returns:
            str: Název vygenerovaného souboru nebo None při chybě
        """
        if not text.strip():
            logger.warning("Empty text provided for TTS generation")
            return None
        
        if not self.provider:
            logger.error("No TTS provider available")
            return None
        
        filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            logger.info(f"Generating audio using {self.provider.get_provider_name()}")
            self.provider.generate(text, output_path)
            
            # Verify file was created
            if not os.path.exists(output_path):
                logger.error(f"Audio file not created: {output_path}")
                return None
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Audio generated successfully: {filename} ({file_size} bytes)")
            
            return filename
            
        except Exception as e:
            logger.error(f"TTS Generation failed: {e}")
            
            # Cleanup on error
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            
            return None

__all__ = ['BaseTTS', 'EdgeTTS', 'ElevenLabsTTS', 'PollyTTS', 'TTSService']
