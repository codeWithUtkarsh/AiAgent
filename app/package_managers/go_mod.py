import subprocess
import re
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import PackageInfo, PackageManager
from app.package_managers.base import BasePackageManager
from app.mcp_client import get_mcp_client


class GoPackageManager(BasePackageManager):
    """Go modules package manager implementation"""

    def detect(self) -> bool:
        """Detect if go modules is used"""
        return self.file_exists("go.mod")

    def get_package_manager_type(self) -> PackageManager:
        """Get package manager type"""
        return PackageManager.GO_MOD

    def _parse_go_mod(self) -> List[Tuple[str, str]]:
        """
        Parse go.mod file to extract dependencies and their versions

        Returns:
            List of tuples (package_name, current_version)
        """
        go_mod_path = self.repo_path / "go.mod"
        if not go_mod_path.exists():
            return []

        dependencies = []

        try:
            with open(go_mod_path, 'r') as f:
                content = f.read()

            # Pattern to match require block and individual require statements
            # Matches: github.com/package/name v1.2.3
            version_pattern = re.compile(r'^\s*([^\s]+)\s+v([0-9]+\.[0-9]+\.[0-9]+[^\s]*)', re.MULTILINE)

            matches = version_pattern.findall(content)

            for package_name, version in matches:
                # Skip commented lines and invalid entries
                if not package_name.startswith('//') and '/' in package_name:
                    dependencies.append((package_name, version))
                    self.logger.debug(f"Found dependency: {package_name} v{version}")

            self.logger.info(f"Parsed {len(dependencies)} dependencies from go.mod")
            return dependencies

        except Exception as e:
            self.logger.error(f"Error parsing go.mod: {e}")
            return []

    async def _get_latest_version_from_mcp(self, package_name: str) -> Optional[str]:
        """
        Fetch the latest version of a Go package using MCP server

        Args:
            package_name: Full package name (e.g., github.com/gin-gonic/gin)

        Returns:
            Latest version string or None if not found
        """
        try:
            mcp_client = await get_mcp_client()
            version = await mcp_client.check_go_package(package_name)

            if version:
                self.logger.debug(f"Found latest version for {package_name}: v{version}")
                return version
            else:
                self.logger.warning(f"Could not find version for {package_name} via MCP")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching latest version for {package_name}: {e}")
            return None

    async def get_outdated_packages(self) -> List[PackageInfo]:
        """
        Get outdated go packages using MCP server

        This method:
        1. Parses go.mod to get current dependencies
        2. Uses MCP server to check each package's latest version
        3. Compares versions and returns outdated packages
        """
        self.logger.info("Checking for outdated go packages via MCP server")

        try:
            # Parse go.mod to get current dependencies
            dependencies = self._parse_go_mod()

            if not dependencies:
                self.logger.warning("No dependencies found in go.mod")
                return []

            self.logger.info(f"Checking {len(dependencies)} dependencies for updates")

            packages = []

            # Check each dependency for updates
            for package_name, current_version in dependencies:
                self.logger.info(f"Checking {package_name} (current: v{current_version})")

                # Fetch latest version from MCP server
                latest_version = await self._get_latest_version_from_mcp(package_name)

                if latest_version is None:
                    self.logger.warning(f"Could not determine latest version for {package_name}")
                    continue

                # Compare versions (remove 'v' prefix if present for comparison)
                current_clean = current_version.lstrip('v')
                latest_clean = latest_version.lstrip('v')

                if current_clean != latest_clean:
                    # Simple version comparison - if they're different, consider it outdated
                    # More sophisticated comparison could use semver library
                    if self._is_version_outdated(current_clean, latest_clean):
                        packages.append(PackageInfo(
                            name=package_name,
                            current_version=current_version,
                            latest_version=latest_version,
                            is_outdated=True
                        ))
                        self.logger.info(f"✓ {package_name}: v{current_version} → v{latest_version} (outdated)")
                    else:
                        self.logger.info(f"✓ {package_name}: v{current_version} is up to date or newer")
                else:
                    self.logger.info(f"✓ {package_name}: v{current_version} is up to date")

            self.logger.info(f"Found {len(packages)} outdated packages")
            return packages

        except Exception as e:
            self.logger.error(f"Error checking outdated packages: {e}")
            return []

    def _is_version_outdated(self, current: str, latest: str) -> bool:
        """
        Compare two semantic versions to determine if current is outdated

        Args:
            current: Current version (e.g., "1.2.3")
            latest: Latest version (e.g., "1.3.0")

        Returns:
            True if current < latest
        """
        try:
            # Split versions into parts
            current_parts = [int(x.split('-')[0].split('+')[0]) for x in current.split('.')]
            latest_parts = [int(x.split('-')[0].split('+')[0]) for x in latest.split('.')]

            # Pad to same length
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)

            # Compare major.minor.patch
            for i in range(min(3, len(current_parts))):
                if current_parts[i] < latest_parts[i]:
                    return True
                elif current_parts[i] > latest_parts[i]:
                    return False

            return False  # Versions are equal

        except (ValueError, IndexError) as e:
            self.logger.warning(f"Error comparing versions {current} and {latest}: {e}")
            # If we can't parse, assume it's different and thus outdated
            return current != latest

    async def update_packages(
        self,
        packages: Optional[List[str]] = None,
        outdated_packages: Optional[List[PackageInfo]] = None
    ) -> Tuple[bool, str]:
        """
        Update go packages by directly modifying go.mod file

        This method:
        1. Reads go.mod file
        2. Gets list of outdated packages (or uses provided list)
        3. Updates version numbers in go.mod content
        4. Writes updated content back to go.mod
        """
        self.logger.info("Updating go packages by modifying go.mod")

        try:
            # Use provided outdated packages or fetch them
            if outdated_packages is not None:
                self.logger.info(f"Using provided list of {len(outdated_packages)} outdated packages")
                outdated = outdated_packages
            else:
                self.logger.info("Fetching outdated packages...")
                outdated = await self.get_outdated_packages()

            if not outdated:
                return True, "No outdated packages to update"

            # Read go.mod
            go_mod_path = self.repo_path / "go.mod"
            if not go_mod_path.exists():
                return False, "go.mod not found"

            with open(go_mod_path, 'r') as f:
                original_content = f.read()

            # Make a copy to modify
            updated_content = original_content
            updated_packages = []
            outputs = []
            actual_changes = False

            # Update each package version in the file
            for pkg in outdated:
                if packages and pkg.name not in packages:
                    continue

                self.logger.info(f"Updating {pkg.name} from v{pkg.current_version} to v{pkg.latest_version}")

                # Pattern to match the package line in go.mod
                # Matches: "package_name v1.2.3" and replaces with "package_name v1.2.4"
                old_version = pkg.current_version.lstrip('v')
                new_version = pkg.latest_version.lstrip('v')

                # Create regex pattern that matches the package line
                # Handle both formats: "pkg v1.2.3" and "pkg v1.2.3 // indirect"
                pattern = re.compile(
                    rf'({re.escape(pkg.name)}\s+)v{re.escape(old_version)}(\s|$|//)',
                    re.MULTILINE
                )

                # Replace the version
                new_content, count = pattern.subn(rf'\1v{new_version}\2', updated_content)

                if count > 0:
                    updated_content = new_content
                    updated_packages.append(pkg.name)
                    actual_changes = True
                    outputs.append(f"✓ Updated {pkg.name}: v{old_version} → v{new_version}")
                    self.logger.info(f"Successfully updated {pkg.name} in go.mod")
                else:
                    outputs.append(f"⚠ Could not find {pkg.name} v{old_version} in go.mod")
                    self.logger.warning(f"Could not find pattern for {pkg.name} in go.mod")

            if not actual_changes:
                self.logger.warning("No actual changes made to go.mod")
                return True, "Package versions already at target versions"

            # Write updated content back to go.mod
            with open(go_mod_path, 'w') as f:
                f.write(updated_content)

            self.logger.info(f"Updated go.mod with {len(updated_packages)} packages")

            output = f"Updated {len(updated_packages)} packages in go.mod:\n\n"
            output += "\n".join(outputs)
            output += f"\n\nNote: go.sum will be regenerated when you run 'go mod tidy' or build the project."

            return True, output

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
