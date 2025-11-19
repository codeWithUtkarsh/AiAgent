import subprocess
import re
import json
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import PackageInfo, PackageManager
from app.package_managers.base import BasePackageManager
from app.mcp_client import get_mcp_client


class PipPackageManager(BasePackageManager):
    """Pip package manager implementation"""

    def detect(self) -> bool:
        """Detect if pip is used"""
        return (
            self.file_exists("requirements.txt") or
            self.file_exists("setup.py") or
            self.file_exists("pyproject.toml")
        )

    def get_package_manager_type(self) -> PackageManager:
        """Get package manager type"""
        if self.file_exists("poetry.lock"):
            return PackageManager.POETRY
        elif self.file_exists("Pipfile"):
            return PackageManager.PIPENV
        else:
            return PackageManager.PIP

    async def get_outdated_packages(self) -> List[PackageInfo]:
        """
        Get outdated pip packages using MCP server

        Uses the MCP package version server to check for outdated packages.
        This provides a more reliable and consistent way to check package versions
        compared to running pip commands.
        """
        self.logger.info("Checking for outdated pip packages using MCP server")

        try:
            # Parse requirements.txt to get current packages
            if not self.file_exists("requirements.txt"):
                self.logger.warning("requirements.txt not found")
                return []

            requirements_content = self.read_file("requirements.txt")
            if not requirements_content:
                self.logger.warning("Could not read requirements.txt")
                return []

            packages = []
            mcp_client = await get_mcp_client()

            # Parse each line of requirements.txt
            for line in requirements_content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Extract package name and version
                # Handle formats like: package==1.0.0, package>=1.0.0, package~=1.0.0, package
                match = re.match(r'^([a-zA-Z0-9\-_\.]+)\s*([=<>~!]+)?\s*(.+)?', line)
                if match:
                    pkg_name = match.group(1)
                    current_version = match.group(3) if match.group(3) else None

                    # Check latest version via MCP
                    latest_version = await mcp_client.check_pypi_package(pkg_name)

                    if latest_version and current_version:
                        # Clean version string
                        current_clean = current_version.strip()
                        if current_clean != latest_version:
                            packages.append(PackageInfo(
                                name=pkg_name,
                                current_version=current_clean,
                                latest_version=latest_version,
                                is_outdated=True
                            ))
                            self.logger.info(f"Found outdated package: {pkg_name} {current_clean} -> {latest_version}")

            self.logger.info(f"Found {len(packages)} outdated packages via MCP")
            return packages

        except Exception as e:
            self.logger.error(f"Error checking outdated packages via MCP: {e}")
            return []

    async def update_packages(
        self,
        packages: Optional[List[str]] = None,
        outdated_packages: Optional[List[PackageInfo]] = None
    ) -> Tuple[bool, str]:
        """Update pip packages"""
        self.logger.info("Updating pip packages")

        try:
            if not self.file_exists("requirements.txt"):
                return False, "requirements.txt not found"

            # Read current requirements
            requirements_content = self.read_file("requirements.txt")
            if not requirements_content:
                return False, "Could not read requirements.txt"

            # Use provided outdated packages or fetch them
            if outdated_packages is not None:
                self.logger.info(f"Using provided list of {len(outdated_packages)} outdated packages")
                outdated = outdated_packages
            else:
                self.logger.info("Fetching outdated packages...")
                outdated = await self.get_outdated_packages()

            if not outdated:
                return True, "No packages to update"

            # Update requirements.txt with new versions
            updated_lines = []
            for line in requirements_content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    updated_lines.append(line)
                    continue

                # Extract package name
                match = re.match(r'^([a-zA-Z0-9\-_\.]+)', line)
                if match:
                    pkg_name = match.group(1)
                    # Find if this package is outdated
                    outdated_pkg = next(
                        (p for p in outdated if p.name.lower() == pkg_name.lower()),
                        None
                    )
                    if outdated_pkg and outdated_pkg.latest_version:
                        updated_lines.append(f"{pkg_name}=={outdated_pkg.latest_version}")
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)

            # Write updated requirements.txt
            requirements_path = self.repo_path / "requirements.txt"
            requirements_path.write_text("\n".join(updated_lines) + "\n")

            self.logger.info("Successfully updated requirements.txt")
            return True, f"Updated {len(outdated)} packages in requirements.txt"

        except Exception as e:
            error_msg = f"Error updating packages: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_lockfile_paths(self) -> List[Path]:
        """Get lock file paths"""
        lockfiles = []

        if self.file_exists("requirements.txt"):
            lockfiles.append(self.repo_path / "requirements.txt")
        if self.file_exists("poetry.lock"):
            lockfiles.append(self.repo_path / "poetry.lock")
        if self.file_exists("Pipfile.lock"):
            lockfiles.append(self.repo_path / "Pipfile.lock")

        return lockfiles

    def get_main_dependency_file(self) -> Optional[str]:
        """Get the main dependency file"""
        if self.file_exists("pyproject.toml"):
            return "pyproject.toml"
        elif self.file_exists("requirements.txt"):
            return "requirements.txt"
        elif self.file_exists("Pipfile"):
            return "Pipfile"
        return None
