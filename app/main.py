from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.config import get_settings
from app.logger import setup_logger, get_logger
import uvicorn

# Initialize settings
settings = get_settings()

# Setup logger
setup_logger("ai_agent", settings.log_level)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Dependency Update Agent",
    description="""
    An intelligent AI agent that automatically updates package dependencies in your repositories.

    ## Features

    * **Automatic Package Manager Detection**: Supports npm, pip, cargo, and more
    * **Intelligent Updates**: Uses Anthropic's Claude to analyze and document updates
    * **Pull Request Creation**: Automatically creates PRs with comprehensive descriptions
    * **Real-time Tracking**: Monitor job progress with detailed logs

    ## Workflow

    1. Submit a repository URL via `/api/update`
    2. The agent clones the repository and detects the package manager
    3. Identifies outdated packages
    4. Updates them and creates a new branch
    5. Generates an AI-powered PR description
    6. Creates a pull request on GitHub

    ## Usage

    1. **Create Update Job**: POST `/api/update` with repository URL
    2. **Check Status**: GET `/api/jobs/{job_id}` to monitor progress
    3. **View Results**: Get PR URL and update details from job status
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, tags=["AI Agent"])


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("=" * 60)
    logger.info("AI Dependency Update Agent Starting")
    logger.info("=" * 60)
    logger.info(f"Host: {settings.app_host}")
    logger.info(f"Port: {settings.app_port}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Workspace: {settings.workspace_dir}")
    logger.info(f"Model: {settings.anthropic_model}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("AI Dependency Update Agent Shutting Down")

    # Close MCP client if it's running
    try:
        from app.mcp_client import close_mcp_client
        await close_mcp_client()
        logger.info("MCP client closed successfully")
    except Exception as e:
        logger.warning(f"Error closing MCP client: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )


def main():
    """Main entry point"""
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
