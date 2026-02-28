"""
Translation Service: Sarvam AI Text Translation.

Translates text from Indian languages to English using Sarvam AI.
"""
import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Service for translating text from Indian languages to English using Sarvam AI.
    
    Supports 22 Indian languages including Hindi, Tamil, Telugu, Malayalam, Kannada, etc.
    """
    
    BASE_URL = "https://api.sarvam.ai/translate"
    
    def __init__(self):
        """Initialize the translation service with Sarvam API key."""
        self.api_key = os.getenv("SARVAM_API_KEY")
        if not self.api_key:
            logger.warning("SARVAM_API_KEY not found in environment variables")
    
    async def translate_to_english(
        self, 
        text: str, 
        source_language: str = "auto"
    ) -> Optional[str]:
        """
        Translate text from an Indian language to English.
        
        Args:
            text: The text to translate
            source_language: Source language code (e.g., 'hi-IN', 'ta-IN', 'ml-IN')
                           Use 'auto' for automatic language detection (mayura:v1 only)
        
        Returns:
            Translated English text, or None if translation fails
        """
        if not self.api_key:
            logger.error("Cannot translate: SARVAM_API_KEY not configured")
            return None
        
        if not text or not text.strip():
            logger.warning("Empty text provided for translation")
            return text
        
        try:
            logger.info(f"Translating text from {source_language} to English")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers={
                        "api-subscription-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": text[:2000],  # Max 2000 characters
                        "source_language_code": source_language,
                        "target_language_code": "en-IN",
                        "model": "mayura:v1",  # Supports auto-detection
                        "mode": "formal"
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                translated_text = result.get("translated_text", "")
                detected_lang = result.get("source_language_code", "unknown")
                
                logger.info(f"Translation successful. Detected language: {detected_lang}")
                return translated_text
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during translation: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return None
    
    async def detect_and_translate(self, text: str) -> tuple[str, bool]:
        """
        Detect language and translate to English if needed.
        
        Args:
            text: Input text in any language
        
        Returns:
            Tuple of (translated_text, was_translated)
            - If already in English, returns (original_text, False)
            - If translated, returns (translated_text, True)
        """
        # Try translation with auto-detection
        translated = await self.translate_to_english(text, source_language="auto")
        
        if translated and translated != text:
            logger.info("Text was translated from regional language to English")
            return translated, True
        else:
            logger.info("Text appears to be in English already")
            return text, False
