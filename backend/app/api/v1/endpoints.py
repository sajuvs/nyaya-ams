"""
API v1 Endpoints for Legal Aid Generation.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ...models.schemas import LegalAidRequest, LegalAidResponse
from ...services.orchestrator import LegalAidOrchestrator

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
        result = await orchestrator.generate_legal_aid(
            grievance=request.grievance,
            rag_context=request.rag_context
        )
        
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
            "agents": ["researcher", "drafter", "expert_reviewer"]
        }
    )
