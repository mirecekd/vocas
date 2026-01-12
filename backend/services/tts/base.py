"""
Abstraktní třída pro TTS poskytovatele
"""
from abc import ABC, abstractmethod


class BaseTTS(ABC):
    """
    Abstraktní třída pro TTS poskytovatele.
    """
    
    @abstractmethod
    def generate(self, text: str, output_path: str) -> str:
        """
        Generuje audio z textu.
        
        Args:
            text: Text k přečtení
            output_path: Cesta k výstupnímu audio souboru
        
        Returns:
            str: Cesta k vygenerovanému souboru
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Vrátí název poskytovatele.
        
        Returns:
            str: Název poskytovatele
        """
        pass
