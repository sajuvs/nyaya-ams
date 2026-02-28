"""Configuration for audio transcription service."""

import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class TranscriptionConfig:
    """Configuration for Sarvam AI transcription service."""
    
    # Sarvam AI Configuration
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    
    # Audio Processing Settings
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    SILENCE_DURATION_MS: int = 1000  # 1 second silence for Sarvam API
    
    # Transcription Settings
    LANGUAGE_CODE: str = "unknown"  # Auto-detect language
    MODEL: str = "saaras:v3"  # Latest and most accurate model
    
    # Queue Settings
    MAX_RECENT_TRANSCRIPTIONS: int = 50
    MAX_PROCESSED_CHUNKS: int = 1000
    
    # API Settings
    API_TIMEOUT: float = 10.0  # seconds
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.SARVAM_API_KEY:
            raise ValueError("SARVAM_API_KEY environment variable is required")
        return True


# Create singleton instance
config = TranscriptionConfig()
