"""
AWS Polly TTS implementace
"""
import boto3
from .base import BaseTTS
import os


class PollyTTS(BaseTTS):
    """
    AWS Polly TTS provider.
    """
    
    def __init__(self, voice_id: str = 'Iveta', region: str = 'eu-central-1'):
        """
        Inicializace AWS Polly TTS.
        
        Args:
            voice_id: ID hlasu (default: 'Iveta' - český ženský hlas)
            region: AWS region (default: 'eu-central-1')
        """
        self.voice_id = voice_id
        self.region = region
        
        # Vytvoření Polly klienta
        self.client = boto3.client(
            'polly',
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
    
    def generate(self, text: str, output_path: str) -> str:
        """
        Generuje audio z textu pomocí AWS Polly.
        
        Args:
            text: Text k přečtení
            output_path: Cesta k výstupnímu MP3 souboru
        
        Returns:
            str: Cesta k vygenerovanému souboru
        """
        # Volání Polly API
        response = self.client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=self.voice_id,
            Engine='neural'  # Neural engine pro lepší kvalitu
        )
        
        # Uložení audio streamu
        with open(output_path, 'wb') as f:
            f.write(response['AudioStream'].read())
        
        return output_path
    
    def get_provider_name(self) -> str:
        """
        Vrátí název poskytovatele.
        
        Returns:
            str: Název poskytovatele
        """
        return f"aws-polly (voice={self.voice_id}, region={self.region})"
