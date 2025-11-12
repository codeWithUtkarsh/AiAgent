import subprocess
import re
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import PackageInfo, PackageManager
from app.package_managers.base import BasePackageManager


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
        """Get outdated pip packages"""
        self.logger.info("Checking for outdated pip packages")

        try:
            # Install dependencies first if requirements.txt exists
            if self.file_exists("requirements.txt"):
                subprocess.run(
                    ["pip", "install", "-r", "requirements.txt"],
                    cwd=self.repo_path,
                    capture_output=True,
                    timeout=300
                )

            # Run pip list --outdated
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                self.logger.error(f"pip list --outdated failed: {result.stderr}")
                return []

            import json
            outdated_data = json.loads(result.stdout)
            packages = []

            for pkg in outdated_data:
                packages.append(PackageInfo(
                    name=pkg["name"],
                    current_version=pkg["version"],
                    latest_version=pkg["latest_version"],
                    is_outdated=True
                ))

            self.logger.info(f"Found {len(packages)} outdated packages")
            return packages

        except subprocess.TimeoutExpired:
            self.logger.error("pip command timed out")
            return []
        except FileNotFoundError:
            self.logger.error("pip command not found")
            return []
        except Exception as e:
            self.logger.error(f"Error checking outdated packages: {e}")
            return []

    async def update_packages(self, packages: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Update pip packages"""
        self.logger.info("Updating pip packages")

        try:
            if not self.file_exists("requirements.txt"):
                return False, "requirements.txt not found"

            # Read current requirements
            requirements_content = self.read_file("requirements.txt")
            if not requirements_content:
                return False, "Could not read requirements.txt"

            # Get list of outdated packages
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
