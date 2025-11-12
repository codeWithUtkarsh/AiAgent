import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from git import Repo, GitCommandError
from app.logger import get_logger

logger = get_logger(__name__)


class GitService:
    """Service for Git operations"""

    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger

    def clone_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None
    ) -> Tuple[Optional[Repo], Optional[Path]]:
        """
        Clone a repository to workspace

        Args:
            repo_url: Repository URL
            branch: Branch to clone (optional)

        Returns:
            Tuple of (Repo object, Path to cloned repo)
        """
        try:
            # Extract repo name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            clone_path = self.workspace_dir / repo_name

            # Remove existing directory if it exists
            if clone_path.exists():
                self.logger.info(f"Removing existing repository at {clone_path}")
                shutil.rmtree(clone_path)

            self.logger.info(f"Cloning repository {repo_url} to {clone_path}")

            # Clone repository
            if branch:
                repo = Repo.clone_from(
                    repo_url,
                    clone_path,
                    branch=branch,
                    depth=1
                )
            else:
                repo = Repo.clone_from(repo_url, clone_path, depth=1)

            self.logger.info(f"Successfully cloned repository to {clone_path}")
            return repo, clone_path

        except GitCommandError as e:
            self.logger.error(f"Git error while cloning: {e}")
            return None, None
        except Exception as e:
            self.logger.error(f"Error cloning repository: {e}")
            return None, None

    def create_branch(self, repo: Repo, branch_name: str) -> bool:
        """
        Create a new branch

        Args:
            repo: Git repository object
            branch_name: Name of the branch to create

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Creating branch: {branch_name}")

            # Create and checkout new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()

            self.logger.info(f"Successfully created and checked out branch: {branch_name}")
            return True

        except GitCommandError as e:
            self.logger.error(f"Git error while creating branch: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error creating branch: {e}")
            return False

    def commit_changes(
        self,
        repo: Repo,
        files: list,
        commit_message: str
    ) -> bool:
        """
        Commit changes to repository

        Args:
            repo: Git repository object
            files: List of files to commit
            commit_message: Commit message

        Returns:
            True if successful, False otherwise
        """
        try:
            # Filter out files that don't exist
            existing_files = []
            for file in files:
                file_path = Path(file)
                if file_path.exists():
                    existing_files.append(file)
                    self.logger.debug(f"Will commit: {file}")
                else:
                    self.logger.warning(f"Skipping non-existent file: {file}")

            if not existing_files:
                self.logger.warning("No files to commit")
                return False

            self.logger.info(f"Committing {len(existing_files)} files")

            # Add files
            for file in existing_files:
                # Convert to relative path from repo root
                repo_root = Path(repo.working_dir)
                try:
                    relative_path = Path(file).relative_to(repo_root)
                    repo.index.add([str(relative_path)])
                except ValueError:
                    # If file is already relative or absolute path outside repo
                    repo.index.add([str(file)])

            # Check if there are any changes to commit
            if not repo.index.diff("HEAD"):
                self.logger.info("No changes to commit")
                return True

            # Commit
            repo.index.commit(commit_message)

            self.logger.info("Successfully committed changes")
            return True

        except GitCommandError as e:
            self.logger.error(f"Git error while committing: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error committing changes: {e}")
            return False

    def push_changes(
        self,
        repo: Repo,
        branch_name: str,
        github_token: Optional[str] = None
    ) -> bool:
        """
        Push changes to remote repository

        Args:
            repo: Git repository object
            branch_name: Branch name to push
            github_token: GitHub token for authentication

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Pushing branch: {branch_name}")

            # Set up authentication if token provided
            if github_token:
                # Get remote URL
                origin = repo.remote('origin')
                url = origin.url

                # Add token to URL
                if url.startswith('https://'):
                    authenticated_url = url.replace(
                        'https://',
                        f'https://{github_token}@'
                    )
                    origin.set_url(authenticated_url)

            # Push changes
            origin = repo.remote('origin')
            origin.push(refspec=f'{branch_name}:{branch_name}')

            self.logger.info(f"Successfully pushed branch: {branch_name}")
            return True

        except GitCommandError as e:
            self.logger.error(f"Git error while pushing: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error pushing changes: {e}")
            return False

    def cleanup_repository(self, repo_path: Path):
        """
        Clean up cloned repository

        Args:
            repo_path: Path to repository to clean up
        """
        try:
            if repo_path.exists():
                self.logger.info(f"Cleaning up repository at {repo_path}")
                shutil.rmtree(repo_path)
        except Exception as e:
            self.logger.error(f"Error cleaning up repository: {e}")
