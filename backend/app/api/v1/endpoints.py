"""API v1 Endpoints for Legal Aid Generation."""
import logging
from typing import Dict
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
from config.domain_loader import DomainLoader

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
        logger.info(f"Received request for domain '{request.domain}': {request.grievance[:100]}...")
        
        orchestrator = LegalAidOrchestrator(domain=request.domain)
        result = await orchestrator.generate_legal_aid(grievance=request.grievance)
        
        logger.info(f"Generation complete. Status: {result['status']}")
        return LegalAidResponse(**result)
        
    except FileNotFoundError as e:
        logger.error(f"Domain not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )


@router.get(
    "/domains",
    status_code=status.HTTP_200_OK,
    summary="List Available Domains",
    description="Get list of all available domain configurations"
)
async def list_domains():
    """List all available domains."""
    try:
        domains = DomainLoader.list_available_domains()
        return JSONResponse(
            content={
                "domains": domains,
                "total": len(domains)
            }
        )
    except Exception as e:
        logger.error(f"Error listing domains: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list domains: {str(e)}"
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
    description="Start workflow and return research findings for human review"
)
async def start_legal_aid(request: LegalAidRequest) -> Dict:
    """Start workflow with research phase."""
    try:
        logger.info(f"Starting HITL workflow for domain '{request.domain}': {request.grievance[:100]}...")
        
        orchestrator = LegalAidOrchestrator(domain=request.domain)
        result = await orchestrator.start_research(request.grievance)
        
        logger.info(f"Research complete. Session: {result['session_id']}")
        return result
        
    except FileNotFoundError as e:
        logger.error(f"Domain not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.post(
    "/approve-research",
    status_code=status.HTTP_200_OK,
    summary="Approve Research Findings",
    description="Approve/edit research and continue to drafting phase"
)
async def approve_research(request: ResearchApprovalRequest) -> Dict:
    """Continue workflow with approved research."""
    try:
        logger.info(f"Research approved for session: {request.session_id}")
        
        # Get session to retrieve domain
        session = WorkflowState.get_session(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")
        
        domain = session.get("domain", "legal_ai")
        orchestrator = LegalAidOrchestrator(domain=domain)
        result = await orchestrator.continue_with_draft(
            request.session_id,
            request.approved_research
        )
        
        logger.info(f"Draft generated for session: {request.session_id}")
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error approving research: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve research: {str(e)}"
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
        
        # Get session to retrieve domain
        session = WorkflowState.get_session(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")
        
        domain = session.get("domain", "legal_ai")
        orchestrator = LegalAidOrchestrator(domain=domain)
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
        
        # Get session to retrieve domain
        session = WorkflowState.get_session(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")
        
        domain = session.get("domain", "legal_ai")
        orchestrator = LegalAidOrchestrator(domain=domain)
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
