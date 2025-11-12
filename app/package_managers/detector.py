from pathlib import Path
from typing import Optional, List
from app.models import PackageManager
from app.package_managers.base import BasePackageManager
from app.package_managers.npm import NpmPackageManager
from app.package_managers.pip import PipPackageManager
from app.package_managers.cargo import CargoPackageManager
from app.logger import get_logger

logger = get_logger(__name__)


class PackageManagerDetector:
    """Detects and creates appropriate package manager instances"""

    # Order matters - more specific detectors should come first
    PACKAGE_MANAGERS = [
        NpmPackageManager,
        PipPackageManager,
        CargoPackageManager,
    ]

    @classmethod
    def detect(cls, repo_path: Path) -> Optional[BasePackageManager]:
        """
        Detect which package manager is used in the repository

        Args:
            repo_path: Path to the repository

        Returns:
            Appropriate package manager instance or None if not detected
        """
        logger.info(f"Detecting package manager in {repo_path}")

        for pm_class in cls.PACKAGE_MANAGERS:
            pm_instance = pm_class(repo_path)
            if pm_instance.detect():
                pm_type = pm_instance.get_package_manager_type()
                logger.info(f"Detected package manager: {pm_type.value}")
                return pm_instance

        logger.warning("No package manager detected")
        return None

    @classmethod
    def get_all_package_managers(cls, repo_path: Path) -> List[BasePackageManager]:
        """
        Get all detected package managers (for monorepos)

        Args:
            repo_path: Path to the repository

        Returns:
            List of detected package managers
        """
        managers = []
        for pm_class in cls.PACKAGE_MANAGERS:
            pm_instance = pm_class(repo_path)
            if pm_instance.detect():
                managers.append(pm_instance)

        return managers
