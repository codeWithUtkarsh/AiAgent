import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from app.models import (
    JobStatus,
    JobStatusResponse,
    PackageManager,
    PackageInfo,
    UpdateRequest
)
from app.services.git_service import GitService
from app.services.github_service import GitHubService
from app.services.anthropic_agent import AnthropicAgent
from app.package_managers.detector import PackageManagerDetector
from app.logger import get_logger

logger = get_logger(__name__)


class UpdateOrchestrator:
    """Main orchestrator for dependency update workflow"""

    def __init__(
        self,
        anthropic_api_key: Optional[str],
        github_token: Optional[str],
        workspace_dir: str,
        branch_prefix: str = "dependency-updates"
    ):
        self.git_service = GitService(workspace_dir)
        self.github_service = GitHubService(github_token) if github_token else None
        self.ai_agent = AnthropicAgent(anthropic_api_key)
        self.branch_prefix = branch_prefix
        self.logger = logger
        self.github_token = github_token

        # Job tracking
        self.jobs: Dict[str, JobStatusResponse] = {}

    def create_job(self, request: UpdateRequest) -> str:
        """Create a new job"""
        job_id = str(uuid.uuid4())

        job = JobStatusResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            repository_url=str(request.repository_url),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            logs=[]
        )

        self.jobs[job_id] = job
        self.logger.info(f"Created job {job_id} for {request.repository_url}")

        return job_id

    def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """Get job status"""
        return self.jobs.get(job_id)

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        log_message: Optional[str] = None,
        **kwargs
    ):
        """Update job status"""
        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]
        job.status = status
        job.updated_at = datetime.now()

        if log_message:
            job.logs.append(f"[{datetime.now().isoformat()}] {log_message}")

        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        self.logger.info(f"Job {job_id}: {status.value} - {log_message}")

    async def process_update(self, job_id: str, request: UpdateRequest):
        """
        Process dependency update request

        Args:
            job_id: Job ID
            request: Update request
        """
        repo = None
        repo_path = None

        try:
            # Step 1: Clone repository
            self.update_job_status(
                job_id,
                JobStatus.CLONING,
                f"Cloning repository {request.repository_url}"
            )

            repo, repo_path = self.git_service.clone_repository(
                str(request.repository_url),
                request.branch
            )

            if not repo or not repo_path:
                raise Exception("Failed to clone repository")

            self.update_job_status(
                job_id,
                JobStatus.DETECTING,
                "Repository cloned successfully"
            )

            # Step 2: Detect package manager
            self.update_job_status(
                job_id,
                JobStatus.DETECTING,
                "Detecting package manager"
            )

            package_manager = PackageManagerDetector.detect(repo_path)

            if not package_manager:
                raise Exception("No supported package manager detected")

            pm_type = package_manager.get_package_manager_type()
            self.update_job_status(
                job_id,
                JobStatus.DETECTING,
                f"Detected package manager: {pm_type.value}",
                package_manager=pm_type
            )

            # Step 3: Check for outdated packages
            self.update_job_status(
                job_id,
                JobStatus.ANALYZING,
                "Checking for outdated packages"
            )

            outdated_packages = await package_manager.get_outdated_packages()

            if not outdated_packages:
                self.update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    "No outdated packages found",
                    outdated_packages=outdated_packages
                )
                return

            self.update_job_status(
                job_id,
                JobStatus.ANALYZING,
                f"Found {len(outdated_packages)} outdated packages",
                outdated_packages=outdated_packages
            )

            # Step 4: Analyze updates with AI
            analysis = await self.ai_agent.analyze_package_updates(
                pm_type,
                outdated_packages
            )

            self.update_job_status(
                job_id,
                JobStatus.ANALYZING,
                f"AI Analysis: {analysis}"
            )

            # Step 5: Create new branch
            branch_name = f"{self.branch_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            if not self.git_service.create_branch(repo, branch_name):
                raise Exception("Failed to create branch")

            self.update_job_status(
                job_id,
                JobStatus.UPDATING,
                f"Created branch: {branch_name}"
            )

            # Step 6: Update packages
            self.update_job_status(
                job_id,
                JobStatus.UPDATING,
                "Updating packages"
            )

            success, output = await package_manager.update_packages()

            if not success:
                raise Exception(f"Package update failed: {output}")

            self.update_job_status(
                job_id,
                JobStatus.UPDATING,
                "Packages updated successfully",
                updated_packages=outdated_packages
            )

            # Step 7: Commit changes
            lockfiles = package_manager.get_lockfile_paths()
            commit_message = await self.ai_agent.generate_commit_message(
                pm_type,
                outdated_packages
            )

            if not self.git_service.commit_changes(repo, lockfiles, commit_message):
                raise Exception("Failed to commit changes")

            self.update_job_status(
                job_id,
                JobStatus.UPDATING,
                "Changes committed"
            )

            # Step 8: Push changes (if creating PR)
            if request.create_pr:
                # Get GitHub token from github_service
                github_token = self.github_service.github.get_user().raw_headers.get('Authorization', '').replace('token ', '')

                if not self.git_service.push_changes(repo, branch_name, github_token):
                    # Try without token
                    if not self.git_service.push_changes(repo, branch_name):
                        raise Exception("Failed to push changes")

                self.update_job_status(
                    job_id,
                    JobStatus.CREATING_PR,
                    f"Pushed branch: {branch_name}"
                )

                # Step 9: Create pull request
                owner, repo_name = self.github_service.parse_repo_url(
                    str(request.repository_url)
                )

                if not owner or not repo_name:
                    raise Exception("Failed to parse repository URL")

                # Get base branch
                base_branch = request.branch or self.github_service.get_default_branch(
                    owner,
                    repo_name
                )

                if not base_branch:
                    base_branch = "main"

                # Generate PR description
                pr_description = await self.ai_agent.generate_pr_description(
                    pm_type,
                    outdated_packages,
                    output
                )

                pr_title = f"chore: Update {pm_type.value} dependencies ({len(outdated_packages)} packages)"

                pr_url = self.github_service.create_pull_request(
                    owner,
                    repo_name,
                    pr_title,
                    pr_description,
                    branch_name,
                    base_branch
                )

                if not pr_url:
                    raise Exception("Failed to create pull request")

                self.update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    f"Pull request created: {pr_url}",
                    pr_url=pr_url
                )
            else:
                self.update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    "Updates completed (no PR created)"
                )

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Job {job_id} failed: {error_msg}")
            self.update_job_status(
                job_id,
                JobStatus.FAILED,
                f"Error: {error_msg}",
                error=error_msg
            )

        finally:
            # Cleanup
            if repo_path:
                self.git_service.cleanup_repository(repo_path)
