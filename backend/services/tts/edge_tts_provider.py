"""
Microsoft Edge TTS implementace
"""
import logging
import edge_tts
import asyncio
from .base import BaseTTS

logger = logging.getLogger(__name__)

# Edge TTS intermittently returns NoAudioReceived (voice-specific), so each voice is retried
ATTEMPTS_PER_VOICE = 2


class EdgeTTS(BaseTTS):
    """
    Microsoft Edge TTS provider (zdarma, online).
    Nabízí kvalitní české hlasy.
    """
    
    def __init__(self, voice: str = 'cs-CZ-AntoninNeural', rate: str = '+0%', pitch: str = '+0Hz',
                 fallback_voice: str = ''):
        """
        Inicializace Edge TTS.
        
        Args:
            voice: Hlas (default: 'cs-CZ-AntoninNeural' - mužský český hlas)
                   Další české hlasy:
                   - cs-CZ-VlastaNeural (ženský)
                   - cs-CZ-AntoninNeural (mužský)
            rate: Rychlost řeči (default: '+0%', možnosti: '-50%' až '+100%')
            pitch: Výška hlasu (default: '+0Hz', možnosti: '-50Hz' až '+50Hz')
            fallback_voice: Záložní hlas, když hlavní hlas opakovaně selže (prázdné = žádný)
        """
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.fallback_voice = fallback_voice
    
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
        voices = [self.voice]
        if self.fallback_voice and self.fallback_voice != self.voice:
            voices.append(self.fallback_voice)

        last_error: Exception | None = None
        for voice in voices:
            for attempt in range(1, ATTEMPTS_PER_VOICE + 1):
                try:
                    communicate = edge_tts.Communicate(
                        text=text, voice=voice, rate=self.rate, pitch=self.pitch
                    )
                    await communicate.save(output_path)
                    if voice != self.voice:
                        logger.warning(f"Edge TTS used fallback voice {voice}")
                    return
                except edge_tts.exceptions.NoAudioReceived as e:
                    last_error = e
                    logger.warning(f"Edge TTS {voice} attempt {attempt}/{ATTEMPTS_PER_VOICE}: {e}")
        assert last_error is not None
        raise last_error

    def get_provider_name(self) -> str:
        """
        Vrátí název poskytovatele.
        
        Returns:
            str: Název poskytovatele
        """
        return f"edge-tts (voice={self.voice}, rate={self.rate})"
