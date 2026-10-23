# backend/services/llm.py
import logging

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, api_key: str | None, model: str = 'gemini-3.1-flash-lite'):
        if not api_key:
            logger.warning("Google Gemini API Key not provided!")

        self.model_name = model
        self.client = genai.Client(api_key=api_key) if api_key else None
        # Gemini 3.x thinks at "medium" by default (~2x slower); text cleanup needs no deep reasoning
        # shortcut: thinking_level is only valid for 3.x models, other models use their defaults
        self.config = (
            types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="low"))
            if model.startswith("gemini-3") else None
        )
        logger.info(f"LLM model: {model}")

    def _generate(self, prompt: str) -> str:
        assert self.client is not None  # callers check self.client first
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt, config=self.config
        )
        return response.text or ""

    def clean_text(self, text: str) -> str:
        """
        Uses LLM to clean text for reading (remove dates, weather, etc.)
        """
        if not self.client:
            return text # Fallback if no API key

        system_prompt = """
        You are a text cleaner preparing a web page for Text-to-Speech reading.
        Your job is to FILTER the text, not to rewrite or summarize it.

        Instructions:
        1. Keep the complete article body: its title, lead paragraph and EVERY paragraph.
           Reproduce the article text VERBATIM - same wording, same order, same length.
           NEVER shorten, summarize, paraphrase or merge paragraphs.
        2. REMOVE only non-article content:
           - Dates, times, and name days (e.g., "Dnes je pátek...", "Svátek má...").
           - Weather reports.
           - Navigation menus, subscribe buttons, ads, cookie notices, related-article lists, comments, footers.
           - Image captions (unless essential to the story).
           - Author bylines and publication metadata.
        3. You may only make tiny edits needed for listening: write symbols and abbreviations the
           way they are spoken, and drop URLs and markup.
        4. Keep the original language (do not translate).
        5. Return ONLY the cleaned text. Do not add "Here is the cleaned text:" etc.
        """

        try:
            result = self._generate(f"{system_prompt}\n\nTEXT:\n{text}")
            return result.strip() or text
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
            result = self._generate(f"{system_prompt}\n\nTEXT:\n{text}")
            return result.strip() or "Nepodařilo se vytvořit souhrn."
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return "Chyba při komunikaci s AI."
