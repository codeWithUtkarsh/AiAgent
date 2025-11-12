import json
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import PackageInfo, PackageManager
from app.package_managers.base import BasePackageManager


class NpmPackageManager(BasePackageManager):
    """NPM package manager implementation"""

    def detect(self) -> bool:
        """Detect if npm is used"""
        return self.file_exists("package.json")

    def get_package_manager_type(self) -> PackageManager:
        """Get package manager type"""
        if self.file_exists("pnpm-lock.yaml"):
            return PackageManager.PNPM
        elif self.file_exists("yarn.lock"):
            return PackageManager.YARN
        else:
            return PackageManager.NPM

    async def get_outdated_packages(self) -> List[PackageInfo]:
        """Get outdated npm packages"""
        self.logger.info("Checking for outdated npm packages")

        try:
            # Run npm outdated --json
            result = subprocess.run(
                ["npm", "outdated", "--json"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # npm outdated returns non-zero exit code when there are outdated packages
            if not result.stdout:
                self.logger.info("No outdated packages found")
                return []

            outdated_data = json.loads(result.stdout)
            packages = []

            for name, info in outdated_data.items():
                packages.append(PackageInfo(
                    name=name,
                    current_version=info.get("current", "unknown"),
                    latest_version=info.get("latest", "unknown"),
                    is_outdated=True
                ))

            self.logger.info(f"Found {len(packages)} outdated packages")
            return packages

        except subprocess.TimeoutExpired:
            self.logger.error("npm outdated command timed out")
            return []
        except json.JSONDecodeError:
            self.logger.error("Failed to parse npm outdated output")
            return []
        except FileNotFoundError:
            self.logger.error("npm command not found")
            return []
        except Exception as e:
            self.logger.error(f"Error checking outdated packages: {e}")
            return []

    async def update_packages(self, packages: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Update npm packages"""
        self.logger.info("Updating npm packages")

        try:
            # First, install dependencies
            install_result = subprocess.run(
                ["npm", "install"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if install_result.returncode != 0:
                error_msg = f"npm install failed: {install_result.stderr}"
                self.logger.error(error_msg)
                return False, error_msg

            # Update packages
            if packages:
                # Update specific packages
                cmd = ["npm", "update"] + packages
            else:
                # Update all packages
                cmd = ["npm", "update"]

            update_result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if update_result.returncode != 0:
                error_msg = f"npm update failed: {update_result.stderr}"
                self.logger.error(error_msg)
                return False, error_msg

            output = f"STDOUT:\n{update_result.stdout}\n\nSTDERR:\n{update_result.stderr}"
            self.logger.info("Successfully updated npm packages")
            return True, output

        except subprocess.TimeoutExpired:
            error_msg = "npm update command timed out"
            self.logger.error(error_msg)
            return False, error_msg
        except FileNotFoundError:
            error_msg = "npm command not found"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error updating packages: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_lockfile_paths(self) -> List[Path]:
        """Get lock file paths"""
        lockfiles = []

        # Always include package.json first
        if self.file_exists("package.json"):
            lockfiles.append(self.repo_path / "package.json")

        # Add lock files if they exist
        if self.file_exists("package-lock.json"):
            lockfiles.append(self.repo_path / "package-lock.json")
        if self.file_exists("yarn.lock"):
            lockfiles.append(self.repo_path / "yarn.lock")
        if self.file_exists("pnpm-lock.yaml"):
            lockfiles.append(self.repo_path / "pnpm-lock.yaml")

        # Log which files were found
        self.logger.info(f"Found {len(lockfiles)} files to commit: {[f.name for f in lockfiles]}")

        return lockfiles
