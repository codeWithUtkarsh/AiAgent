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
            # First, read package.json to get current version specifiers
            package_json_path = self.repo_path / "package.json"
            current_versions = {}

            if package_json_path.exists():
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)

                    # Get versions from dependencies
                    if "dependencies" in package_data:
                        for name, version in package_data["dependencies"].items():
                            current_versions[name] = version

                    # Get versions from devDependencies
                    if "devDependencies" in package_data:
                        for name, version in package_data["devDependencies"].items():
                            if name not in current_versions:
                                current_versions[name] = version

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
                # Try to get current version from multiple sources
                current_version = (
                    info.get("current") or  # From npm outdated
                    current_versions.get(name) or  # From package.json
                    "unknown"
                )

                packages.append(PackageInfo(
                    name=name,
                    current_version=current_version,
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

            # Get outdated packages to update
            outdated = await self.get_outdated_packages()
            if not outdated:
                return True, "No outdated packages to update"

            # Read package.json
            package_json_path = self.repo_path / "package.json"
            if not package_json_path.exists():
                return False, "package.json not found"

            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            # Track which packages we're updating
            updated_packages = []

            # Update version specifiers in package.json for outdated packages
            for pkg in outdated:
                updated_in_deps = False
                updated_in_dev_deps = False

                # Check and update in dependencies
                if "dependencies" in package_data and pkg.name in package_data["dependencies"]:
                    old_version = package_data["dependencies"][pkg.name]
                    package_data["dependencies"][pkg.name] = f"^{pkg.latest_version}"
                    updated_packages.append(pkg.name)
                    updated_in_deps = True
                    self.logger.info(f"Updated {pkg.name} in dependencies: {old_version} -> ^{pkg.latest_version}")

                # Check and update in devDependencies
                if "devDependencies" in package_data and pkg.name in package_data["devDependencies"]:
                    old_version = package_data["devDependencies"][pkg.name]
                    package_data["devDependencies"][pkg.name] = f"^{pkg.latest_version}"
                    if not updated_in_deps:
                        updated_packages.append(pkg.name)
                    updated_in_dev_deps = True
                    self.logger.info(f"Updated {pkg.name} in devDependencies: {old_version} -> ^{pkg.latest_version}")

                if not updated_in_deps and not updated_in_dev_deps:
                    self.logger.warning(f"Package {pkg.name} not found in dependencies or devDependencies")

            if not updated_packages:
                return True, "No packages were updated in package.json"

            # Write updated package.json
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
                f.write('\n')  # Add newline at end of file

            self.logger.info(f"Updated package.json with {len(updated_packages)} packages: {', '.join(updated_packages)}")

            # Now run npm install to actually install the new versions
            install_result = subprocess.run(
                ["npm", "install"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if install_result.returncode != 0:
                error_msg = f"npm install after update failed: {install_result.stderr}"
                self.logger.error(error_msg)
                return False, error_msg

            output = f"Updated {len(updated_packages)} packages: {', '.join(updated_packages)}\n\n"
            output += f"STDOUT:\n{install_result.stdout}\n\nSTDERR:\n{install_result.stderr}"
            self.logger.info(f"Successfully updated {len(updated_packages)} npm packages")
            return True, output

        except subprocess.TimeoutExpired:
            error_msg = "npm command timed out"
            self.logger.error(error_msg)
            return False, error_msg
        except FileNotFoundError:
            error_msg = "npm command not found"
            self.logger.error(error_msg)
            return False, error_msg
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse package.json: {e}"
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

    def get_main_dependency_file(self) -> Optional[str]:
        """Get the main dependency file"""
        return "package.json"
