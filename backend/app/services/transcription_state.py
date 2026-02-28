"""State management for transcription sessions."""

import logging
from typing import Dict, Any, List, Set
from datetime import datetime
from collections import deque

from ..config.transcription_config import config

logger = logging.getLogger(__name__)


class TranscriptionState:
    """
    In-memory state management for transcription sessions.
    
    Tracks:
    - Active client connections
    - Recent transcriptions (for polling fallback)
    - Processed chunks (for deduplication)
    """
    
    # Active WebSocket clients
    _active_clients: Set[str] = set()
    
    # Recent transcriptions queue (for polling fallback)
    _recent_transcriptions: deque = deque(maxlen=config.MAX_RECENT_TRANSCRIPTIONS)
    
    # Processed chunks (for deduplication)
    _processed_chunks: Set[str] = set()
    
    @classmethod
    def add_client(cls, client_id: str):
        """Add a client to active connections."""
        cls._active_clients.add(client_id)
        logger.info(f"Client connected: {client_id}. Total clients: {len(cls._active_clients)}")
    
    @classmethod
    def remove_client(cls, client_id: str):
        """Remove a client from active connections."""
        cls._active_clients.discard(client_id)
        logger.info(f"Client disconnected: {client_id}. Total clients: {len(cls._active_clients)}")
    
    @classmethod
    def get_active_clients(cls) -> Set[str]:
        """Get all active client IDs."""
        return cls._active_clients.copy()
    
    @classmethod
    def add_transcription(cls, transcription_data: Dict[str, Any]):
        """
        Add a transcription to the recent queue.
        
        Args:
            transcription_data: Dictionary with transcription details
        """
        cls._recent_transcriptions.append(transcription_data)
        logger.info(f"Added transcription to queue. Queue size: {len(cls._recent_transcriptions)}")
    
    @classmethod
    def get_recent_transcriptions(cls) -> List[Dict[str, Any]]:
        """Get all recent transcriptions."""
        return list(cls._recent_transcriptions)
    
    @classmethod
    def clear_transcriptions(cls):
        """Clear all transcriptions from queue."""
        cls._recent_transcriptions.clear()
        logger.info("Transcription queue cleared")
    
    @classmethod
    def is_chunk_processed(cls, chunk_name: str) -> bool:
        """
        Check if a chunk has already been processed.
        
        Args:
            chunk_name: Unique identifier for the audio chunk
            
        Returns:
            True if already processed, False otherwise
        """
        return chunk_name in cls._processed_chunks
    
    @classmethod
    def mark_chunk_processed(cls, chunk_name: str):
        """
        Mark a chunk as processed.
        
        Args:
            chunk_name: Unique identifier for the audio chunk
        """
        cls._processed_chunks.add(chunk_name)
        
        # Prevent memory leak by limiting set size
        if len(cls._processed_chunks) > config.MAX_PROCESSED_CHUNKS:
            logger.info("Processed chunks limit reached. Clearing old chunks.")
            cls._processed_chunks.clear()
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        Get current state statistics.
        
        Returns:
            Dictionary with state statistics
        """
        return {
            "active_clients": len(cls._active_clients),
            "recent_transcriptions": len(cls._recent_transcriptions),
            "processed_chunks": len(cls._processed_chunks),
            "timestamp": datetime.utcnow().isoformat()
        }
