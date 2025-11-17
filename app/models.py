from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class PackageManager(str, Enum):
    """
    Package managers detected by AI.

    All package managers are handled by GenericPackageManager which uses AI
    to parse, search, and update any dependency file format.
    """
    GENERIC = "generic"
    UNKNOWN = "unknown"


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    CLONING = "cloning"
    DETECTING = "detecting"
    ANALYZING = "analyzing"
    UPDATING = "updating"
    CREATING_PR = "creating_pr"
    COMPLETED = "completed"
    FAILED = "failed"


class PackageInfo(BaseModel):
    """Information about a package"""
    name: str
    current_version: str
    latest_version: Optional[str] = None
    is_outdated: bool = False


class UpdateRequest(BaseModel):
    """Request to update repository dependencies"""
    repository_url: HttpUrl = Field(
        ...,
        description="GitHub repository URL (e.g., https://github.com/owner/repo)"
    )
    branch: Optional[str] = Field(
        default=None,
        description="Target branch (defaults to repository's default branch)"
    )
    create_pr: bool = Field(
        default=True,
        description="Whether to create a pull request"
    )


class UpdateResponse(BaseModel):
    """Response for update request"""
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: JobStatus
    repository_url: str
    package_manager: Optional[PackageManager] = None
    outdated_packages: List[PackageInfo] = []
    updated_packages: List[PackageInfo] = []
    pr_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    logs: List[str] = []


class AnalysisResult(BaseModel):
    """Result of dependency analysis"""
    package_manager: PackageManager
    outdated_packages: List[PackageInfo]
    total_packages: int
    update_summary: str
