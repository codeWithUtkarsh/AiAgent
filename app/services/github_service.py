from typing import Optional, Tuple
from github import Github, GithubException
from app.logger import get_logger

logger = get_logger(__name__)


class GitHubService:
    """Service for GitHub API operations"""

    def __init__(self, github_token: str):
        self.github = Github(github_token)
        self.logger = logger

    def parse_repo_url(self, repo_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse repository URL to extract owner and repo name

        Args:
            repo_url: GitHub repository URL

        Returns:
            Tuple of (owner, repo_name)
        """
        try:
            # Handle various URL formats
            # https://github.com/owner/repo
            # https://github.com/owner/repo.git
            # git@github.com:owner/repo.git

            url = repo_url.strip()

            if url.startswith('git@github.com:'):
                # SSH format
                parts = url.replace('git@github.com:', '').replace('.git', '').split('/')
            elif 'github.com/' in url:
                # HTTPS format
                parts = url.split('github.com/')[-1].replace('.git', '').split('/')
            else:
                self.logger.error(f"Invalid GitHub URL format: {repo_url}")
                return None, None

            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1]
                return owner, repo_name

            self.logger.error(f"Could not parse repository URL: {repo_url}")
            return None, None

        except Exception as e:
            self.logger.error(f"Error parsing repository URL: {e}")
            return None, None

    def get_default_branch(self, owner: str, repo_name: str) -> Optional[str]:
        """
        Get the default branch of a repository

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            Default branch name or None
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            return repo.default_branch
        except GithubException as e:
            self.logger.error(f"GitHub API error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting default branch: {e}")
            return None

    def create_pull_request(
        self,
        owner: str,
        repo_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str
    ) -> Optional[str]:
        """
        Create a pull request

        Args:
            owner: Repository owner
            repo_name: Repository name
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch

        Returns:
            PR URL or None if failed
        """
        try:
            self.logger.info(f"Creating pull request: {title}")

            repo = self.github.get_repo(f"{owner}/{repo_name}")

            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )

            self.logger.info(f"Successfully created PR: {pr.html_url}")
            return pr.html_url

        except GithubException as e:
            self.logger.error(f"GitHub API error while creating PR: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating pull request: {e}")
            return None

    def check_repository_access(self, owner: str, repo_name: str) -> bool:
        """
        Check if we have access to the repository

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            True if accessible, False otherwise
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            # Try to access a property to verify access
            _ = repo.name
            return True
        except GithubException as e:
            self.logger.error(f"No access to repository: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking repository access: {e}")
            return False
