import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, api_key: str, model: str = 'gemini-2.5-flash'):
        if not api_key:
            logger.warning("Google Gemini API Key not provided!")
        else:
            genai.configure(api_key=api_key)
        
        self.model_name = model
        self.client = genai.GenerativeModel(model_name=model) if api_key else None

    def clean_text(self, text: str) -> str:
        """
        Uses LLM to clean text for reading (remove dates, weather, etc.)
        """
        if not self.client:
            return text # Fallback if no API key
            
        system_prompt = """
        You are an expert news reader assistant. Your task is to prepare the following text for Text-to-Speech reading.
        
        Instructions:
        1. Extract the main journalistic content (the story).
        2. REMOVE:
           - Dates, times, and name days (e.g., "Dnes je pátek...", "Svátek má...").
           - Weather reports.
           - Navigation menus, subscribe buttons, ads.
           - Image captions (unless essential to the story).
           - Author bylines at the start.
        3. Keep the language Czech (or the original language).
        4. Make the text flow naturally for listening.
        5. Return ONLY the cleaned text. Do not add "Here is the cleaned text:" etc.
        """
        
        try:
            response = self.client.generate_content(f"{system_prompt}\n\nTEXT:\n{text}")
            if response.text:
                return response.text.strip()
            return text
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return text

    def summarize_text(self, text: str) -> str:
        """
        Uses LLM to summarize the text.
        """
        if not self.client:
            return "Omlouvám se, ale nemám nastavený API klíč pro sumarizaci."
            
        system_prompt = """
        You are an expert news summarizer. 
        
        Instructions:
        1. Create a concise summary of the following text in Czech language.
        2. Focus on the most important facts.
        3. Keep it suitable for listening (approx. 3-5 sentences).
        4. Return ONLY the summary.
        """
        
        try:
            response = self.client.generate_content(f"{system_prompt}\n\nTEXT:\n{text}")
            if response.text:
                return response.text.strip()
            return "Nepodařilo se vytvořit souhrn."
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return "Chyba při komunikaci s AI."
