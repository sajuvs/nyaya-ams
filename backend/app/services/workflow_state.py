"""Workflow state management for Human-in-the-Loop."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


class WorkflowState:
    """In-memory workflow state storage (use Redis/DB in production)."""
    
    _sessions: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def create_session(cls, grievance: str) -> str:
        """Create a new workflow session."""
        session_id = str(uuid4())
        cls._sessions[session_id] = {
            "session_id": session_id,
            "grievance": grievance,
            "stage": "started",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Created workflow session: {session_id}")
        return session_id
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        return cls._sessions.get(session_id)
    
    @classmethod
    def update_session(cls, session_id: str, data: Dict[str, Any]):
        """Update session with new data."""
        if session_id in cls._sessions:
            cls._sessions[session_id].update(data)
            cls._sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
            logger.info(f"Updated session {session_id}: stage={data.get('stage')}")
    
    @classmethod
    def delete_session(cls, session_id: str):
        """Delete a session."""
        if session_id in cls._sessions:
            del cls._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
