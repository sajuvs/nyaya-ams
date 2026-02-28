"""API v1 Endpoints for Legal Aid Generation."""
import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ...models.schemas import (
    LegalAidRequest, 
    LegalAidResponse,
    ResearchApprovalRequest,
    DraftReviewRequest,
    FinalizeRequest,
    WorkflowStatusResponse
)
from ...services.orchestrator import LegalAidOrchestrator
from ...services.workflow_state import WorkflowState
from ...services.transcription_state import TranscriptionState
from ...services.translation_service import TranslationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["legal-aid"])


@router.post(
    "/generate-legal-aid",
    response_model=LegalAidResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Legal Aid Document",
    description="""
    Generate a formal legal petition through multi-agent collaboration.
    
    This endpoint orchestrates three AI agents:
    1. Researcher: Analyzes the grievance and identifies applicable laws
    2. Drafter: Creates a formal legal petition
    3. Expert Reviewer: Audits the draft for compliance
    
    The system includes a self-correction loop where rejected drafts
    are automatically refined based on expert feedback.
    """
)
async def generate_legal_aid(request: LegalAidRequest) -> LegalAidResponse:
    """
    Generate a legal aid document with multi-agent workflow.
    
    Args:
        request: Contains the user's grievance and optional RAG context
        
    Returns:
        Complete legal aid response with document, traces, and metadata
        
    Raises:
        HTTPException: If the generation process fails
    """
    try:
        logger.info(f"Received legal aid request: {request.grievance[:100]}...")
        
        orchestrator = LegalAidOrchestrator()
        result = await orchestrator.generate_legal_aid(grievance=request.grievance)
        
        logger.info(f"Legal aid generation complete. Status: {result['status']}")
        return LegalAidResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating legal aid: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate legal aid: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API is running and agents are initialized"
)
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "Nyaya-Flow Legal Aid API",
            "version": "1.0.0",
            "agents": ["researcher", "drafter", "expert_reviewer"],
            "mode": "human-in-the-loop"
        }
    )


# ===== HUMAN-IN-THE-LOOP ENDPOINTS =====

@router.post(
    "/start-legal-aid",
    status_code=status.HTTP_200_OK,
    summary="Start Legal Aid Workflow",
    description="Start workflow and return research findings for human review. Automatically translates regional language input to English."
)
async def start_legal_aid(request: LegalAidRequest) -> Dict:
    """Start workflow with research phase. Translates input if needed."""
    try:
        logger.info(f"Starting HITL workflow: {request.grievance[:100]}...")
        
        # Translate if needed
        translation_service = TranslationService()
        translated_text, was_translated = await translation_service.detect_and_translate(request.grievance)
        
        if was_translated:
            logger.info("Input was translated from regional language to English")
        
        orchestrator = LegalAidOrchestrator()
        result = await orchestrator.start_research(translated_text)
        result["is_approved"] = request.is_approved
        result["was_translated"] = was_translated
        result["original_text"] = request.grievance if was_translated else None
        
        logger.info(f"Research complete. Session: {result['session_id']}")
        return result
    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.post(
    "/approve-research",
    status_code=status.HTTP_200_OK,
    summary="Approve or Reject Research Findings",
    description="is_approved=True proceeds to drafting, is_approved=False re-runs research"
)
async def approve_research(request: ResearchApprovalRequest) -> Dict:
    """Continue or re-run based on human approval."""
    try:
        orchestrator = LegalAidOrchestrator()
        if request.is_approved:
            logger.info(f"Research approved for session: {request.session_id}")
            result = await orchestrator.continue_with_draft(
                request.session_id,
                request.approved_research
            )
            result["is_approved"] = True
        else:
            logger.info(f"Research rejected, re-running for session: {request.session_id}")
            session = WorkflowState.get_session(request.session_id)
            if not session:
                raise ValueError(f"Session {request.session_id} not found")
            # Reset stage and re-run research
            WorkflowState.update_session(request.session_id, {"stage": "awaiting_research_approval"})
            result = await orchestrator.start_research(session["grievance"])
            new_session_id = result["session_id"]
            # Copy new session data into original session, delete the new one
            new_session = WorkflowState.get_session(new_session_id)
            if new_session:
                WorkflowState.update_session(request.session_id, {
                    k: v for k, v in new_session.items() if k != "session_id"
                })
                WorkflowState.delete_session(new_session_id)
            result["session_id"] = request.session_id
            result["is_approved"] = False
        logger.info(f"Research action complete for session: {request.session_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in approve_research: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process research approval: {str(e)}"
        )


@router.post(
    "/review-draft",
    status_code=status.HTTP_200_OK,
    summary="Provide Draft Feedback",
    description="Provide feedback to refine the draft"
)
async def review_draft(request: DraftReviewRequest) -> Dict:
    """Refine draft based on human feedback."""
    try:
        logger.info(f"Draft feedback received for session: {request.session_id}")
        
        orchestrator = LegalAidOrchestrator()
        result = await orchestrator.refine_draft(
            request.session_id,
            request.feedback
        )
        
        logger.info(f"Draft refined for session: {request.session_id}")
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error refining draft: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine draft: {str(e)}"
        )


@router.post(
    "/finalize-legal-aid",
    response_model=LegalAidResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalize Legal Aid Document",
    description="Approve final draft and complete workflow"
)
async def finalize_legal_aid(request: FinalizeRequest) -> LegalAidResponse:
    """Finalize workflow with human approval."""
    try:
        logger.info(f"Finalizing workflow for session: {request.session_id}")
        
        orchestrator = LegalAidOrchestrator()
        result = await orchestrator.finalize_workflow(request.session_id)
        
        logger.info(f"Workflow finalized for session: {request.session_id}")
        return LegalAidResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finalizing workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize workflow: {str(e)}"
        )


@router.get(
    "/workflow-status/{session_id}",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Workflow Status",
    description="Check current status of a workflow session"
)
async def get_workflow_status(session_id: str) -> WorkflowStatusResponse:
    """Get current workflow status."""
    session = WorkflowState.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return WorkflowStatusResponse(
        session_id=session_id,
        stage=session["stage"],
        message=f"Workflow is at stage: {session['stage']}",
        data={"created_at": session["created_at"], "updated_at": session["updated_at"]}
    )


# ===== TRANSCRIPTION ENDPOINTS (Polling Fallback) =====

@router.get(
    "/transcriptions",
    status_code=status.HTTP_200_OK,
    tags=["transcription"],
    summary="Get Recent Transcriptions",
    description="Polling endpoint for transcriptions (WebSocket fallback)"
)
async def get_transcriptions() -> Dict[str, List[Dict]]:
    """
    Get recent transcriptions as polling fallback for WebSocket.
    
    Returns:
        Dictionary with list of recent transcriptions
    """
    transcriptions = TranscriptionState.get_recent_transcriptions()
    return {
        "transcriptions": transcriptions,
        "count": len(transcriptions)
    }


@router.delete(
    "/transcriptions",
    status_code=status.HTTP_200_OK,
    tags=["transcription"],
    summary="Clear Transcriptions",
    description="Clear the transcription queue"
)
async def clear_transcriptions() -> Dict[str, str]:
    """Clear all transcriptions from the queue."""
    TranscriptionState.clear_transcriptions()
    return {"status": "cleared", "message": "Transcription queue cleared"}


@router.get(
    "/transcription-stats",
    status_code=status.HTTP_200_OK,
    tags=["transcription"],
    summary="Get Transcription Statistics",
    description="Get current transcription service statistics"
)
async def get_transcription_stats() -> Dict:
    """
    Get transcription service statistics.
    
    Returns:
        Dictionary with service statistics
    """
    return TranscriptionState.get_stats()
