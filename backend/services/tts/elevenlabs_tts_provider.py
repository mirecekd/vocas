"""
ElevenLabs TTS implementace
"""
from elevenlabs.client import ElevenLabs
from .base import BaseTTS


class ElevenLabsTTS(BaseTTS):
    """
    ElevenLabs TTS provider.
    """
    
    def __init__(
        self, 
        api_key: str,
        voice_id: str,
        model_id: str = 'eleven_multilingual_v2'
    ):
        """
        Inicializace ElevenLabs TTS.
        
        Args:
            api_key: ElevenLabs API klíč
            voice_id: ID hlasu z ElevenLabs
            model_id: ID modelu (default: 'eleven_multilingual_v2')
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        
        # Vytvoření klienta
        self.client = ElevenLabs(api_key=api_key)
    
    def generate(self, text: str, output_path: str) -> str:
        """
        Generuje audio z textu pomocí ElevenLabs.
        
        Args:
            text: Text k přečtení
            output_path: Cesta k výstupnímu MP3 souboru
        
        Returns:
            str: Cesta k vygenerovanému souboru
        """
        # Volání ElevenLabs API
        audio_generator = self.client.generate(
            text=text,
            voice=self.voice_id,
            model=self.model_id
        )
        
        # Uložení audio do souboru
        with open(output_path, 'wb') as f:
            for chunk in audio_generator:
                if isinstance(chunk, bytes):
                    f.write(chunk)
        
        return output_path
    
    def get_provider_name(self) -> str:
        """
        Vrátí název poskytovatele.
        
        Returns:
            str: Název poskytovatele
        """
        return f"elevenlabs (voice={self.voice_id}, model={self.model_id})"
