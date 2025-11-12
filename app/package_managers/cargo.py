import subprocess
import toml
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import PackageInfo, PackageManager
from app.package_managers.base import BasePackageManager


class CargoPackageManager(BasePackageManager):
    """Cargo (Rust) package manager implementation"""

    def detect(self) -> bool:
        """Detect if cargo is used"""
        return self.file_exists("Cargo.toml")

    def get_package_manager_type(self) -> PackageManager:
        """Get package manager type"""
        return PackageManager.CARGO

    async def get_outdated_packages(self) -> List[PackageInfo]:
        """Get outdated cargo packages"""
        self.logger.info("Checking for outdated cargo packages")

        try:
            # Run cargo outdated
            result = subprocess.run(
                ["cargo", "outdated", "--format", "json"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                # cargo outdated might not be installed, try alternative
                self.logger.warning("cargo outdated not available, using cargo tree")
                return []

            import json
            outdated_data = json.loads(result.stdout)
            packages = []

            for pkg in outdated_data.get("dependencies", []):
                if pkg.get("latest") and pkg.get("project") != pkg.get("latest"):
                    packages.append(PackageInfo(
                        name=pkg["name"],
                        current_version=pkg.get("project", "unknown"),
                        latest_version=pkg.get("latest"),
                        is_outdated=True
                    ))

            self.logger.info(f"Found {len(packages)} outdated packages")
            return packages

        except FileNotFoundError:
            self.logger.error("cargo command not found")
            return []
        except Exception as e:
            self.logger.error(f"Error checking outdated packages: {e}")
            return []

    async def update_packages(self, packages: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Update cargo packages"""
        self.logger.info("Updating cargo packages")

        try:
            # Run cargo update
            if packages:
                cmd = ["cargo", "update", "-p"] + packages
            else:
                cmd = ["cargo", "update"]

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                error_msg = f"cargo update failed: {result.stderr}"
                self.logger.error(error_msg)
                return False, error_msg

            output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            self.logger.info("Successfully updated cargo packages")
            return True, output

        except subprocess.TimeoutExpired:
            error_msg = "cargo update command timed out"
            self.logger.error(error_msg)
            return False, error_msg
        except FileNotFoundError:
            error_msg = "cargo command not found"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error updating packages: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_lockfile_paths(self) -> List[Path]:
        """Get lock file paths"""
        lockfiles = []

        if self.file_exists("Cargo.lock"):
            lockfiles.append(self.repo_path / "Cargo.lock")
        if self.file_exists("Cargo.toml"):
            lockfiles.append(self.repo_path / "Cargo.toml")

        return lockfiles
