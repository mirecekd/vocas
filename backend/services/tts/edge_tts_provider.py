"""
Microsoft Edge TTS implementace
"""
import edge_tts
import asyncio
from .base import BaseTTS


class EdgeTTS(BaseTTS):
    """
    Microsoft Edge TTS provider (zdarma, online).
    Nabízí kvalitní české hlasy.
    """
    
    def __init__(self, voice: str = 'cs-CZ-AntoninNeural', rate: str = '+0%', pitch: str = '+0Hz'):
        """
        Inicializace Edge TTS.
        
        Args:
            voice: Hlas (default: 'cs-CZ-AntoninNeural' - mužský český hlas)
                   Další české hlasy:
                   - cs-CZ-VlastaNeural (ženský)
                   - cs-CZ-AntoninNeural (mužský)
            rate: Rychlost řeči (default: '+0%', možnosti: '-50%' až '+100%')
            pitch: Výška hlasu (default: '+0Hz', možnosti: '-50Hz' až '+50Hz')
        """
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
    
    def generate(self, text: str, output_path: str) -> str:
        """
        Generuje audio z textu pomocí Edge TTS.
        
        Args:
            text: Text k přečtení
            output_path: Cesta k výstupnímu MP3 souboru
        
        Returns:
            str: Cesta k vygenerovanému souboru
        """
        # Edge TTS je async - musíme ho volat správně
        import asyncio
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running (FastAPI), create a new thread
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(self._generate_async(text, output_path))
            else:
                loop.run_until_complete(self._generate_async(text, output_path))
        except RuntimeError:
            # No event loop, create new one
            asyncio.run(self._generate_async(text, output_path))
        return output_path
    
    async def _generate_async(self, text: str, output_path: str):
        """
        Async generování audio.
        
        Args:
            text: Text k přečtení
            output_path: Cesta k výstupnímu souboru
        """
        # Vytvoření Edge TTS komunikace
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )
        
        # Uložení audio
        await communicate.save(output_path)
    
    def get_provider_name(self) -> str:
        """
        Vrátí název poskytovatele.
        
        Returns:
            str: Název poskytovatele
        """
        return f"edge-tts (voice={self.voice}, rate={self.rate})"
