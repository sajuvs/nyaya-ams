"""
Transcription Service: Real-time audio transcription using Sarvam AI.

Handles audio chunk processing and transcription using Sarvam AI's
streaming speech-to-text API.
"""

import logging
import base64
import tempfile
import os
import wave
from typing import Optional
from sarvamai import AsyncSarvamAI

from ..config.transcription_config import config

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for handling audio transcription with Sarvam AI."""
    
    _instance: Optional['TranscriptionService'] = None
    _client: Optional[AsyncSarvamAI] = None
    
    def __new__(cls):
        """Singleton pattern to reuse Sarvam AI client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the transcription service."""
        if self._client is None:
            if not config.SARVAM_API_KEY:
                logger.warning("SARVAM_API_KEY not set. Transcription will not work.")
            else:
                self._client = AsyncSarvamAI(api_subscription_key=config.SARVAM_API_KEY)
                logger.info("Sarvam AI client initialized")
    
    def _create_silence_base64(self) -> str:
        try:
            num_samples = config.AUDIO_SAMPLE_RATE * config.SILENCE_DURATION_MS // 1000
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                with wave.open(tmp_path, 'w') as wf:
                    wf.setnchannels(config.AUDIO_CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(config.AUDIO_SAMPLE_RATE)
                    wf.writeframes(bytes(num_samples * 2))  # zero-filled bytes
                with open(tmp_path, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"Error creating silence audio: {e}")
            raise
    
    async def transcribe_audio_chunk(self, audio_base64: str) -> str:
        """
        Transcribe an audio chunk using Sarvam AI streaming API.
        
        This follows the exact pattern from the working Flask implementation:
        1. Send audio data first
        2. Send silence second
        3. Receive transcription response
        
        Args:
            audio_base64: Base64 encoded audio data (WAV format)
            
        Returns:
            Transcribed text, or empty string if transcription fails
        """
        if not self._client:
            logger.error("❌ Sarvam AI client not initialized")
            return ""
        
        try:
            logger.info(f"📥 Received audio chunk for transcription, size: {len(audio_base64)} chars")
            
            silence_b64 = self._create_silence_base64()
            logger.info(f"🔇 Created silence audio, size: {len(silence_b64)} chars")
            
            logger.info("🔌 Connecting to AM-S AI streaming API...")
            async with self._client.speech_to_text_streaming.connect(
                language_code=config.LANGUAGE_CODE,
                model=config.MODEL,
            ) as ws:
                # Step 1: Send audio data FIRST
                logger.info("📤 Step 1: Sending audio data to AM-S AI...")
                await ws.transcribe(audio=audio_base64)
                logger.info("✅ Audio data sent successfully")
                
                # Step 2: Send silence SECOND
                logger.info("📤 Step 2: Sending silence to signal end of speech...")
                await ws.transcribe(audio=silence_b64)
                logger.info("✅ Silence sent successfully")
                
                # Step 3: Receive response
                logger.info("⏳ Step 3: Waiting for transcription response from AM-S AI...")
                resp = await ws.recv()
                logger.info(f"📨 Received response from AM-S AI: {resp}")
                
                # Extract transcript from response
                transcription = ""
                if hasattr(resp, "data") and hasattr(resp.data, "transcript"):
                    transcription = resp.data.transcript
                    logger.info(f"✅ Extracted from resp.data.transcript: '{transcription}'")
                elif hasattr(resp, "transcript") and resp.transcript:
                    transcription = resp.transcript
                    logger.info(f"✅ Extracted from resp.transcript: '{transcription}'")
                elif hasattr(resp, "text") and resp.text:
                    transcription = resp.text
                    logger.info(f"✅ Extracted from resp.text: '{transcription}'")
                elif isinstance(resp, str):
                    transcription = resp
                    logger.info(f"✅ Response is string: '{transcription}'")
                else:
                    logger.warning(f"⚠️ Could not extract transcription from response: {resp}")
                
                if transcription and transcription.strip():
                    logger.info(f"🎉 Transcription successful: '{transcription}' (length: {len(transcription)} chars)")
                else:
                    logger.warning("⚠️ Transcription is empty or whitespace only")
                
                return transcription
                
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}", exc_info=True)
            return ""
    
    def validate_audio_format(self, audio_base64: str) -> bool:
        try:
            audio_bytes = base64.b64decode(audio_base64)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            try:
                with wave.open(tmp_path, 'r') as wf:
                    logger.info(f"Audio validation: {wf.getnframes()}frames, {wf.getframerate()}Hz, {wf.getnchannels()} channels")
                return True
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return False


# Create singleton instance
transcription_service = TranscriptionService()
