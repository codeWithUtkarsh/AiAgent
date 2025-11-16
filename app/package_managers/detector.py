from pathlib import Path
from typing import Optional, List
from app.models import PackageManager
from app.package_managers.base import BasePackageManager
from app.package_managers.npm import NpmPackageManager
from app.package_managers.pip import PipPackageManager
from app.package_managers.cargo import CargoPackageManager
from app.package_managers.ai_detector import AIPackageManagerDetector
from app.logger import get_logger

logger = get_logger(__name__)


class PackageManagerDetector:
    """
    Detects and creates appropriate package manager instances.

    Supports two detection modes:
    1. AI-powered detection using Claude (when API key available)
    2. Rule-based detection using hardcoded patterns (fallback)
    """

    # Fallback hardcoded list - used when AI detection unavailable
    PACKAGE_MANAGERS = [
        NpmPackageManager,
        PipPackageManager,
        CargoPackageManager,
    ]

    # Mapping from AI-detected names to implementation classes
    PACKAGE_MANAGER_MAP = {
        'npm': NpmPackageManager,
        'yarn': NpmPackageManager,
        'pnpm': NpmPackageManager,
        'node': NpmPackageManager,
        'nodejs': NpmPackageManager,
        'pip': PipPackageManager,
        'poetry': PipPackageManager,
        'pipenv': PipPackageManager,
        'python': PipPackageManager,
        'cargo': CargoPackageManager,
        'rust': CargoPackageManager,
    }

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize detector with optional AI capabilities

        Args:
            anthropic_api_key: Anthropic API key for AI-powered detection
        """
        self.ai_detector = AIPackageManagerDetector(anthropic_api_key) if anthropic_api_key else None
        self.anthropic_api_key = anthropic_api_key

    @classmethod
    def detect(cls, repo_path: Path, anthropic_api_key: Optional[str] = None) -> Optional[BasePackageManager]:
        """
        Detect which package manager is used in the repository

        Uses AI-powered detection when available, falls back to rule-based detection.

        Args:
            repo_path: Path to the repository
            anthropic_api_key: Optional Anthropic API key for AI detection

        Returns:
            Appropriate package manager instance or None if not detected
        """
        detector = cls(anthropic_api_key)
        return detector._detect_internal(repo_path)

    def _detect_internal(self, repo_path: Path) -> Optional[BasePackageManager]:
        """Internal detection logic"""
        logger.info(f"Detecting package manager in {repo_path}")

        # Try AI-powered detection first (if enabled)
        if self.ai_detector and self.ai_detector.ai_enabled:
            logger.info("Attempting AI-powered package manager detection")
            ai_result = self._detect_with_ai_sync(repo_path)
            if ai_result:
                pm_instance = self._create_package_manager_from_ai(repo_path, ai_result)
                if pm_instance:
                    logger.info(f"✓ AI detected package manager: {pm_instance.get_package_manager_type().value}")
                    return pm_instance
                else:
                    logger.warning("AI detection succeeded but couldn't create package manager instance")

        # Fall back to rule-based detection
        logger.info("Using rule-based package manager detection")
        return self._detect_with_rules(repo_path)

    def _detect_with_ai_sync(self, repo_path: Path) -> Optional[dict]:
        """Synchronous wrapper for AI detection"""
        try:
            import asyncio

            # Try to run async function
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a new loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.ai_detector.detect_with_ai(repo_path))
                        return future.result(timeout=30)
                else:
                    return asyncio.run(self.ai_detector.detect_with_ai(repo_path))
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self.ai_detector.detect_with_ai(repo_path))

        except Exception as e:
            logger.error(f"Error in AI detection: {e}")
            return None

    def _create_package_manager_from_ai(
        self,
        repo_path: Path,
        ai_result: dict
    ) -> Optional[BasePackageManager]:
        """
        Create package manager instance from AI detection result

        Args:
            repo_path: Repository path
            ai_result: Result from AI detection

        Returns:
            Package manager instance or None
        """
        pm_name = ai_result.get('package_manager', '').lower()
        logger.info(f"AI suggested package manager: {pm_name}")

        # Try direct lookup
        if pm_name in self.PACKAGE_MANAGER_MAP:
            pm_class = self.PACKAGE_MANAGER_MAP[pm_name]
            pm_instance = pm_class(repo_path)

            # Verify detection is correct
            if pm_instance.detect():
                logger.info(f"✓ Verified AI suggestion: {pm_name}")
                return pm_instance
            else:
                logger.warning(f"AI suggested {pm_name} but verification failed")

        # Try variations
        if self.ai_detector:
            variations = self.ai_detector.get_package_manager_name_variations(pm_name)
            logger.info(f"Trying variations: {variations}")
            for variation in variations:
                if variation in self.PACKAGE_MANAGER_MAP:
                    pm_class = self.PACKAGE_MANAGER_MAP[variation]
                    pm_instance = pm_class(repo_path)
                    if pm_instance.detect():
                        logger.info(f"✓ Verified AI suggestion via variation: {variation}")
                        return pm_instance

        logger.warning(f"Could not create package manager for AI-detected type: {pm_name}")
        return None

    def _detect_with_rules(self, repo_path: Path) -> Optional[BasePackageManager]:
        """Traditional rule-based detection"""
        for pm_class in self.PACKAGE_MANAGERS:
            pm_instance = pm_class(repo_path)
            if pm_instance.detect():
                pm_type = pm_instance.get_package_manager_type()
                logger.info(f"✓ Rule-based detection found: {pm_type.value}")
                return pm_instance

        logger.warning("No package manager detected by rules")
        return None

    @classmethod
    def get_all_package_managers(
        cls,
        repo_path: Path,
        anthropic_api_key: Optional[str] = None
    ) -> List[BasePackageManager]:
        """
        Get all detected package managers (for monorepos)

        Args:
            repo_path: Path to the repository
            anthropic_api_key: Optional Anthropic API key

        Returns:
            List of detected package managers
        """
        detector = cls(anthropic_api_key)

        # Check if AI detects monorepo
        if detector.ai_detector and detector.ai_detector.ai_enabled:
            ai_result = detector._detect_with_ai_sync(repo_path)
            if ai_result and ai_result.get('is_monorepo'):
                logger.info("✓ AI detected monorepo - scanning for multiple package managers")

        # Scan all known package managers
        managers = []
        for pm_class in cls.PACKAGE_MANAGERS:
            pm_instance = pm_class(repo_path)
            if pm_instance.detect():
                managers.append(pm_instance)

        logger.info(f"Found {len(managers)} package manager(s) in repository")
        return managers
