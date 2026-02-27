"""
FastAPI Application Entry Point for Nyaya-Flow Legal Aid Platform.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .api.v1.endpoints import router as v1_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    logger.info("Starting Nyaya-Flow Legal Aid Platform...")
    logger.info("Multi-Agent System: Researcher, Drafter, Expert Reviewer")
    yield
    logger.info("Shutting down Nyaya-Flow Legal Aid Platform...")


# Initialize FastAPI application
app = FastAPI(
    title="Nyaya-Flow Legal Aid API",
    description="""
    Agentic Legal Aid Platform for Indian Citizens.
    
    This API uses a multi-agent system to generate formal legal petitions:
    - **Researcher Agent**: Analyzes grievances and identifies applicable laws
    - **Drafter Agent**: Creates formal legal petitions
    - **Expert Reviewer Agent**: Audits drafts for compliance
    
    The system includes a self-correction loop for quality assurance.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(v1_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Nyaya-Flow Legal Aid API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
