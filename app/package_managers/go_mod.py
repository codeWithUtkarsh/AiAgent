import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import PackageInfo, PackageManager
from app.package_managers.base import BasePackageManager


class GoPackageManager(BasePackageManager):
    """Go modules package manager implementation"""

    def detect(self) -> bool:
        """Detect if go modules is used"""
        return self.file_exists("go.mod")

    def get_package_manager_type(self) -> PackageManager:
        """Get package manager type"""
        return PackageManager.GO_MOD

    async def get_outdated_packages(self) -> List[PackageInfo]:
        """Get outdated go packages"""
        self.logger.info("Checking for outdated go packages")

        try:
            # Get current module dependencies
            result = subprocess.run(
                ["go", "list", "-u", "-m", "-json", "all"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                self.logger.error(f"go list command failed: {result.stderr}")
                return []

            packages = []

            # Parse JSON output line by line (each line is a separate JSON object)
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                try:
                    import json
                    module = json.loads(line)

                    # Skip main module and modules without updates
                    if module.get("Main"):
                        continue

                    path = module.get("Path", "")
                    current_version = module.get("Version", "")
                    update = module.get("Update")

                    if update and update.get("Version"):
                        latest_version = update["Version"]

                        packages.append(PackageInfo(
                            name=path,
                            current_version=current_version,
                            latest_version=latest_version,
                            is_outdated=True
                        ))

                except json.JSONDecodeError:
                    continue

            self.logger.info(f"Found {len(packages)} outdated packages")
            return packages

        except FileNotFoundError:
            self.logger.error("go command not found")
            return []
        except subprocess.TimeoutExpired:
            self.logger.error("go list command timed out")
            return []
        except Exception as e:
            self.logger.error(f"Error checking outdated packages: {e}")
            return []

    async def update_packages(self, packages: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Update go packages"""
        self.logger.info("Updating go packages")

        try:
            # Get outdated packages to update
            outdated = await self.get_outdated_packages()
            if not outdated:
                return True, "No outdated packages to update"

            # Read go.mod to verify current state
            go_mod_path = self.repo_path / "go.mod"
            if not go_mod_path.exists():
                return False, "go.mod not found"

            with open(go_mod_path, 'r') as f:
                original_content = f.read()

            updated_packages = []
            outputs = []

            # Update each package
            for pkg in outdated:
                if packages and pkg.name not in packages:
                    continue

                self.logger.info(f"Updating {pkg.name} from {pkg.current_version} to {pkg.latest_version}")

                # Use go get to update specific package
                result = subprocess.run(
                    ["go", "get", f"{pkg.name}@{pkg.latest_version}"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    updated_packages.append(pkg.name)
                    outputs.append(f"✓ Updated {pkg.name} to {pkg.latest_version}")
                    self.logger.info(f"Successfully updated {pkg.name}")
                else:
                    outputs.append(f"✗ Failed to update {pkg.name}: {result.stderr}")
                    self.logger.warning(f"Failed to update {pkg.name}: {result.stderr}")

            if not updated_packages:
                return True, "No packages were successfully updated"

            # Run go mod tidy to clean up
            tidy_result = subprocess.run(
                ["go", "mod", "tidy"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if tidy_result.returncode != 0:
                self.logger.warning(f"go mod tidy had issues: {tidy_result.stderr}")
                outputs.append(f"⚠ go mod tidy warning: {tidy_result.stderr}")

            # Verify go.mod was actually changed
            with open(go_mod_path, 'r') as f:
                new_content = f.read()

            if original_content == new_content:
                self.logger.warning("go.mod content did not change after updates")
                return True, "Package versions already at target versions"

            self.logger.info(f"Updated go.mod with {len(updated_packages)} packages")

            output = f"Updated {len(updated_packages)} packages: {', '.join(updated_packages)}\n\n"
            output += "\n".join(outputs)
            return True, output

        except FileNotFoundError:
            error_msg = "go command not found"
            self.logger.error(error_msg)
            return False, error_msg
        except subprocess.TimeoutExpired:
            error_msg = "go command timed out"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error updating packages: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_lockfile_paths(self) -> List[Path]:
        """Get lock file paths"""
        lockfiles = []

        if self.file_exists("go.mod"):
            lockfiles.append(self.repo_path / "go.mod")
        if self.file_exists("go.sum"):
            lockfiles.append(self.repo_path / "go.sum")

        self.logger.info(f"Found {len(lockfiles)} files to commit: {[f.name for f in lockfiles]}")
        return lockfiles

    def get_main_dependency_file(self) -> Optional[str]:
        """Get the main dependency file"""
        return "go.mod"
