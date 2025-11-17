from pathlib import Path
from typing import Optional, List
from app.models import PackageManager
from app.package_managers.base import BasePackageManager
from app.package_managers.go_mod import GoPackageManager
from app.package_managers.ai_detector import AIPackageManagerDetector
from app.logger import get_logger

logger = get_logger(__name__)


class PackageManagerDetector:
    """
    AI-powered package manager detector.

    Uses Claude AI to analyze repository structure and identify dependency files
    without any hardcoded mappings. The AI determines:
    - The dependency file (package.json, go.mod, requirements.txt, Cargo.toml, etc.)
    - The package manager and programming language
    - How to handle updates

    Currently only Go modules has a dedicated implementation.
    """

    # Only supported implementations (can be extended)
    SUPPORTED_FILES = {
        'go.mod': GoPackageManager,
    }

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize detector with AI capabilities

        Args:
            anthropic_api_key: Anthropic API key for AI-powered detection (required)
        """
        self.ai_detector = AIPackageManagerDetector(anthropic_api_key) if anthropic_api_key else None
        self.anthropic_api_key = anthropic_api_key

        if not anthropic_api_key or not self.ai_detector or not self.ai_detector.ai_enabled:
            logger.warning("AI-powered detection requires an Anthropic API key")

    @classmethod
    def detect(cls, repo_path: Path, anthropic_api_key: Optional[str] = None) -> Optional[BasePackageManager]:
        """
        Detect which package manager is used in the repository using pure AI inference

        Args:
            repo_path: Path to the repository
            anthropic_api_key: Anthropic API key for AI detection (required)

        Returns:
            Appropriate package manager instance or None if not detected
        """
        detector = cls(anthropic_api_key)
        return detector._detect_internal(repo_path)

    def _detect_internal(self, repo_path: Path) -> Optional[BasePackageManager]:
        """Internal detection logic - purely AI-driven"""
        logger.info(f"Detecting package manager in {repo_path}")

        # Require AI detection
        if not self.ai_detector or not self.ai_detector.ai_enabled:
            logger.error("AI detection is required but not available. Please provide Anthropic API key.")
            return None

        logger.info("Using AI-powered package manager detection")
        ai_result = self._detect_with_ai_sync(repo_path)

        if not ai_result:
            logger.error("AI detection failed to identify package manager")
            return None

        pm_instance = self._create_package_manager_from_ai(repo_path, ai_result)
        if pm_instance:
            logger.info(f"✓ AI detected package manager: {pm_instance.get_package_manager_type().value}")
            return pm_instance
        else:
            logger.error("Could not create package manager from AI detection result")
            return None

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
            ai_result: Result from AI detection containing 'dependency_file'

        Returns:
            Package manager instance or None
        """
        dependency_file = ai_result.get('dependency_file', '')
        pm_name = ai_result.get('package_manager', '').lower()
        language = ai_result.get('language', '')

        logger.info(f"AI identified - File: {dependency_file}, Manager: {pm_name}, Language: {language}")

        if not dependency_file:
            logger.error("AI did not identify a dependency file")
            return None

        # Check if dependency file exists in repo
        dep_file_path = repo_path / dependency_file
        if not dep_file_path.exists():
            logger.error(f"AI identified '{dependency_file}' but it doesn't exist in repo")
            return None

        logger.info(f"✓ Dependency file exists: {dependency_file}")

        # Check if we have an implementation for this dependency file
        if dependency_file in self.SUPPORTED_FILES:
            pm_class = self.SUPPORTED_FILES[dependency_file]
            pm_instance = pm_class(repo_path)

            # Verify detection is correct
            if pm_instance.detect():
                logger.info(f"✓ Successfully created package manager from dependency file: {dependency_file}")
                return pm_instance
            else:
                logger.warning(f"Dependency file exists but package manager verification failed")
                return None
        else:
            logger.error(
                f"AI identified '{dependency_file}' ({pm_name}) but no implementation exists yet. "
                f"Currently supported: {list(self.SUPPORTED_FILES.keys())}"
            )
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
            anthropic_api_key: Anthropic API key

        Returns:
            List of detected package managers
        """
        detector = cls(anthropic_api_key)

        # For now, just return single detection
        # TODO: Implement monorepo support
        pm = detector._detect_internal(repo_path)
        return [pm] if pm else []
