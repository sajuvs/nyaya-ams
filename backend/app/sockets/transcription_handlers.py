"""
SocketIO event handlers for real-time audio transcription.

Handles WebSocket connections and audio chunk processing.
"""

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

from ..services.transcription_service import transcription_service
from ..services.transcription_state import TranscriptionState

logger = logging.getLogger(__name__)


def register_transcription_handlers(sio):
    """
    Register all transcription-related SocketIO event handlers.
    
    Args:
        sio: SocketIO server instance
    """
    
    @sio.event
    async def connect(sid, environ):
        """
        Handle client connection.
        
        Args:
            sid: Session ID for the connected client
            environ: WSGI environment dictionary
        """
        logger.info(f"Client connected: {sid}")
        TranscriptionState.add_client(sid)
        TranscriptionState.clear_processed_chunks()
        
        await sio.emit('status', {
            'message': 'Connected to transcription service',
            'timestamp': datetime.utcnow().isoformat()
        }, to=sid)
    
    @sio.event
    async def disconnect(sid):
        """
        Handle client disconnection.
        
        Args:
            sid: Session ID for the disconnected client
        """
        logger.info(f"Client disconnected: {sid}")
        TranscriptionState.remove_client(sid)
    
    @sio.event
    async def audio_chunk(sid, data: Dict[str, Any]):
        """
        Handle incoming audio chunk for transcription.
        
        Args:
            sid: Session ID of the client
            data: Dictionary containing:
                - audio: Base64 encoded audio data
                - timestamp: Timestamp of the audio chunk
                - chunkName: Unique identifier for the chunk
        """
        try:
            logger.info(f"Received audio_chunk event from {sid}")
            
            # Extract data
            audio_base64 = data.get('audio')
            timestamp = data.get('timestamp', 0)
            chunk_name = data.get('chunkName', 'Unknown')
            
            # Validate audio data
            if not audio_base64:
                await sio.emit('error', {
                    'message': 'No audio data received',
                    'timestamp': datetime.utcnow().isoformat()
                }, to=sid)
                return
            
            # Check for duplicate chunks
            if TranscriptionState.is_chunk_processed(chunk_name):
                logger.info(f"Skipping already processed chunk: {chunk_name}")
                return
            
            logger.info(f"Processing audio chunk: {chunk_name}")
            
            # Mark chunk as processed
            TranscriptionState.mark_chunk_processed(chunk_name)
            
            # Emit processing status
            await sio.emit('transcription_status', {
                'status': 'processing',
                'timestamp': timestamp,
                'chunkName': chunk_name
            }, to=sid)
            
            # Process transcription in background task
            asyncio.create_task(
                _process_transcription(sio, sid, audio_base64, timestamp, chunk_name)
            )
            
        except Exception as e:
            logger.error(f"Error handling audio chunk: {e}", exc_info=True)
            await sio.emit('error', {
                'message': f'Processing error: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }, to=sid)
    
    logger.info("Transcription SocketIO handlers registered")


async def _process_transcription(
    sio,
    sid: str,
    audio_base64: str,
    timestamp: float,
    chunk_name: str
):
    """
    Background task to process audio transcription.
    
    Args:
        sio: SocketIO server instance
        sid: Session ID of the client
        audio_base64: Base64 encoded audio data
        timestamp: Timestamp of the audio chunk
        chunk_name: Unique identifier for the chunk
    """
    try:
        logger.info(f"Starting transcription for chunk: {chunk_name}")
        
        # Perform transcription
        transcription = await transcription_service.transcribe_audio_chunk(audio_base64)
        
        if transcription and transcription.strip():
            logger.info(f"SUCCESS - Transcription: '{transcription}'")
            result_data = {
                'text': transcription,
                'timestamp': timestamp,
                'status': 'completed',
                'chunkName': chunk_name,
                'processedAt': datetime.utcnow().isoformat()
            }
            TranscriptionState.add_transcription(result_data)
            # Emit directly to the originating sid — don't loop active_clients
            try:
                await sio.emit('transcription_result', result_data, to=sid)
                logger.info(f"Emitted transcription to {sid}")
            except Exception as e:
                logger.error(f"Failed to emit to {sid}: {e}")
        else:
            logger.warning(f"Empty transcription for chunk: {chunk_name}")
            await sio.emit('transcription_status', {
                'status': 'empty',
                'timestamp': timestamp,
                'chunkName': chunk_name,
                'message': 'No speech detected in audio chunk'
            }, to=sid)
            
    except Exception as e:
        logger.error(f"Error processing transcription: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Transcription failed: {str(e)}',
            'timestamp': timestamp,
            'chunkName': chunk_name
        }, to=sid)
