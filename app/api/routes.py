from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
from app.models import (
    UpdateRequest,
    UpdateResponse,
    JobStatusResponse,
    JobStatus,
    PackageManager
)
from app.services.orchestrator import UpdateOrchestrator
from app.config import get_settings
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize orchestrator
settings = get_settings()
orchestrator = UpdateOrchestrator(
    anthropic_api_key=settings.anthropic_api_key,
    github_token=settings.github_token,
    workspace_dir=settings.workspace_dir,
    branch_prefix=settings.default_branch_prefix
)


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint

    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "service": "AI Dependency Update Agent"
    }


@router.post("/api/update", response_model=UpdateResponse)
async def create_update_job(
    request: UpdateRequest,
    background_tasks: BackgroundTasks
) -> UpdateResponse:
    """
    Create a new dependency update job

    This endpoint will:
    1. Clone the repository
    2. Detect the package manager
    3. Find outdated packages
    4. Update them
    5. Create a pull request with AI-generated description

    Args:
        request: Update request containing repository URL and options

    Returns:
        Job information including job_id for tracking
    """
    try:
        logger.info(f"Received update request for {request.repository_url}")

        # Create job
        job_id = orchestrator.create_job(request)

        # Start processing in background
        background_tasks.add_task(
            orchestrator.process_update,
            job_id,
            request
        )

        return UpdateResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Job created successfully. Use the job_id to check status."
        )

    except Exception as e:
        logger.error(f"Error creating update job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create update job: {str(e)}"
        )


@router.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a job

    Args:
        job_id: Job ID returned from create_update_job

    Returns:
        Detailed job status including progress, logs, and results
    """
    job = orchestrator.get_job_status(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    return job


@router.get("/api/jobs", response_model=List[JobStatusResponse])
async def list_jobs() -> List[JobStatusResponse]:
    """
    List all jobs

    Returns:
        List of all jobs
    """
    return list(orchestrator.jobs.values())


@router.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str) -> Dict[str, str]:
    """
    Delete a job from the tracking system

    Args:
        job_id: Job ID to delete

    Returns:
        Success message
    """
    if job_id not in orchestrator.jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    del orchestrator.jobs[job_id]
    logger.info(f"Deleted job {job_id}")

    return {"message": f"Job {job_id} deleted successfully"}


@router.get("/api/supported-package-managers")
async def get_supported_package_managers() -> Dict[str, List[str]]:
    """
    Get list of supported package managers

    Returns:
        List of supported package managers
    """
    return {
        "supported_package_managers": [pm.value for pm in PackageManager if pm != PackageManager.UNKNOWN]
    }
