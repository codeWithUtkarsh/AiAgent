from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import PackageInfo, PackageManager
from app.logger import get_logger

logger = get_logger(__name__)


class BasePackageManager(ABC):
    """Base class for package manager implementations"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.logger = logger

    @abstractmethod
    def detect(self) -> bool:
        """
        Detect if this package manager is used in the repository

        Returns:
            True if package manager is detected, False otherwise
        """
        pass

    @abstractmethod
    def get_package_manager_type(self) -> PackageManager:
        """
        Get the package manager type

        Returns:
            PackageManager enum value
        """
        pass

    @abstractmethod
    async def get_outdated_packages(self) -> List[PackageInfo]:
        """
        Get list of outdated packages

        Returns:
            List of outdated packages
        """
        pass

    @abstractmethod
    async def update_packages(self, packages: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Update packages

        Args:
            packages: List of package names to update. If None, update all.

        Returns:
            Tuple of (success: bool, output: str)
        """
        pass

    @abstractmethod
    def get_lockfile_paths(self) -> List[Path]:
        """
        Get paths to lock files that should be committed

        Returns:
            List of lock file paths
        """
        pass

    @abstractmethod
    def get_main_dependency_file(self) -> Optional[str]:
        """
        Get the main dependency file that contains version specifications

        This is the file that should change when dependencies are updated.
        For npm: package.json
        For pip: requirements.txt
        For cargo: Cargo.toml

        Returns:
            Filename of main dependency file (relative to repo root)
        """
        pass

    def file_exists(self, filename: str) -> bool:
        """Check if a file exists in the repository"""
        return (self.repo_path / filename).exists()

    def read_file(self, filename: str) -> Optional[str]:
        """Read a file from the repository"""
        file_path = self.repo_path / filename
        if file_path.exists():
            return file_path.read_text()
        return None
