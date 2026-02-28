"""Main FastAPI application for Nyaya-Flow."""

import logging
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import router
from app.sockets.transcription_handlers import register_transcription_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create SocketIO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Create FastAPI app
app = FastAPI(
    title="Nyaya-Flow Legal Aid API",
    description="Multi-agent AI system for generating legal aid documents with real-time transcription",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routers
app.include_router(router)

# Register SocketIO handlers
register_transcription_handlers(sio)

# Create ASGI application with SocketIO
socket_app = socketio.ASGIApp(
    sio,
    app,
    socketio_path='socket.io'
)

@app.get("/")
async def root():
    return {
        "message": "Nyaya-Flow Legal Aid API",
        "version": "1.0.0",
        "docs": "/docs",
        "features": {
            "legal_aid": "Multi-agent legal document generation",
            "transcription": "Real-time audio transcription via WebSocket"
        }
    }

@app.get("/health")
async def health_check():
    """Extended health check including transcription service."""
    from app.services.transcription_state import TranscriptionState
    
    stats = TranscriptionState.get_stats()
    
    return {
        "status": "healthy",
        "service": "Nyaya-Flow Legal Aid API",
        "version": "1.0.0",
        "agents": ["researcher", "drafter", "expert_reviewer"],
        "mode": "human-in-the-loop",
        "transcription": {
            "enabled": True,
            "active_clients": stats["active_clients"],
            "websocket_path": "/socket.io"
        }
    }

logger.info("Nyaya-Flow application initialized with transcription support")
