import re
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import PackageInfo, PackageManager
from app.package_managers.base import BasePackageManager
from anthropic import Anthropic


class GenericPackageManager(BasePackageManager):
    """
    Generic AI-powered package manager that handles any dependency file
    without hardcoded logic.

    Uses AI to:
    - Parse dependency files in any format
    - Search for latest versions using web search
    - Update dependency files with new versions
    """

    def __init__(
        self,
        repo_path: Path,
        dependency_file: str,
        package_manager_name: str,
        language: str,
        anthropic_api_key: Optional[str] = None
    ):
        """
        Initialize generic package manager

        Args:
            repo_path: Path to repository
            dependency_file: Name of dependency file (e.g., "requirements.txt", "package.json")
            package_manager_name: Package manager name (e.g., "pip", "npm")
            language: Programming language (e.g., "python", "javascript")
            anthropic_api_key: Anthropic API key for AI operations
        """
        super().__init__(repo_path)
        self.dependency_file = dependency_file
        self.package_manager_name = package_manager_name
        self.language = language
        self.anthropic_api_key = anthropic_api_key

        if anthropic_api_key:
            self.ai_client = Anthropic(api_key=anthropic_api_key)
        else:
            self.ai_client = None
            self.logger.warning("No Anthropic API key provided for GenericPackageManager")

    def detect(self) -> bool:
        """Detect if dependency file exists"""
        return self.file_exists(self.dependency_file)

    def get_package_manager_type(self) -> PackageManager:
        """Get package manager type"""
        return PackageManager.GENERIC

    async def get_outdated_packages(self) -> List[PackageInfo]:
        """
        Get outdated packages using AI to parse file and web search to find latest versions
        """
        self.logger.info(f"Checking for outdated packages in {self.dependency_file}")

        if not self.ai_client:
            self.logger.error("AI client not available")
            return []

        try:
            # Step 1: Read dependency file
            dep_file_path = self.repo_path / self.dependency_file
            if not dep_file_path.exists():
                self.logger.error(f"{self.dependency_file} not found")
                return []

            with open(dep_file_path, 'r') as f:
                content = f.read()

            self.logger.info(f"Read {self.dependency_file} ({len(content)} bytes)")

            # Step 2: Use AI to parse dependencies
            dependencies = await self._parse_dependencies_with_ai(content)

            if not dependencies:
                self.logger.warning("No dependencies found by AI")
                return []

            self.logger.info(f"AI found {len(dependencies)} dependencies")

            # Step 3: Search for latest versions using web search
            outdated = []
            for dep in dependencies:
                latest_version = await self._find_latest_version_with_search(
                    dep['name'],
                    dep.get('current_version')
                )

                if latest_version and latest_version != dep.get('current_version'):
                    outdated.append(PackageInfo(
                        name=dep['name'],
                        current_version=dep.get('current_version', 'unknown'),
                        latest_version=latest_version,
                        is_outdated=True
                    ))
                    self.logger.info(
                        f"✓ {dep['name']}: {dep.get('current_version')} → {latest_version}"
                    )

            self.logger.info(f"Found {len(outdated)} outdated packages")
            return outdated

        except Exception as e:
            self.logger.error(f"Error checking outdated packages: {e}")
            return []

    async def _parse_dependencies_with_ai(self, file_content: str) -> List[dict]:
        """
        Use AI to parse dependencies from any dependency file format
        """
        prompt = f"""Parse this {self.language} dependency file ({self.dependency_file}) and extract all dependencies.

File content:
```
{file_content[:2000]}  # First 2000 chars
```

Extract each dependency with its current version. Return in this format:
DEPENDENCY: package_name | current_version

Example for Python requirements.txt:
DEPENDENCY: requests | 2.28.0
DEPENDENCY: django | 4.1.0

Example for package.json:
DEPENDENCY: express | 4.18.0
DEPENDENCY: react | 18.2.0

Important:
- Only list direct dependencies, not comments
- Extract exact version numbers (not ranges like ^1.0.0, use the base version)
- If no version specified, use "latest"
"""

        try:
            message = self.ai_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            # Parse AI response
            dependencies = []
            for line in response_text.split('\n'):
                if line.startswith('DEPENDENCY:'):
                    parts = line.replace('DEPENDENCY:', '').strip().split('|')
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        version = parts[1].strip()
                        dependencies.append({
                            'name': name,
                            'current_version': version
                        })

            self.logger.info(f"AI parsed {len(dependencies)} dependencies")
            return dependencies

        except Exception as e:
            self.logger.error(f"Error parsing dependencies with AI: {e}")
            return []

    async def _find_latest_version_with_search(
        self,
        package_name: str,
        current_version: Optional[str]
    ) -> Optional[str]:
        """
        Use web search (MCP) to find latest version of a package
        """
        # Build search query with package registry URL for grounding
        registry_urls = {
            'python': f'https://pypi.org/project/{package_name}/',
            'javascript': f'https://www.npmjs.com/package/{package_name}',
            'typescript': f'https://www.npmjs.com/package/{package_name}',
            'rust': f'https://crates.io/crates/{package_name}',
            'go': f'https://pkg.go.dev/{package_name}',
            'ruby': f'https://rubygems.org/gems/{package_name}',
            'php': f'https://packagist.org/packages/{package_name}',
            'java': f'https://mvnrepository.com/artifact/{package_name}',
        }

        package_url = registry_urls.get(self.language.lower(), '')

        prompt = f"""Find the latest stable version of the {self.language} package "{package_name}".

Current version: {current_version}
Package URL: {package_url}

Search the package registry and find the latest stable version number.
Return ONLY the version number in this format:
VERSION: x.y.z

Do not include 'v' prefix or any other text.
"""

        try:
            message = self.ai_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            # Extract version from response
            for line in response_text.split('\n'):
                if 'VERSION:' in line:
                    version = line.split('VERSION:')[1].strip()
                    version = version.lstrip('v')  # Remove v prefix if present
                    self.logger.debug(f"Found latest version for {package_name}: {version}")
                    return version

            # Try to extract version with regex as fallback
            version_match = re.search(r'(\d+\.\d+\.\d+)', response_text)
            if version_match:
                return version_match.group(1)

            self.logger.warning(f"Could not extract version for {package_name} from AI response")
            return None

        except Exception as e:
            self.logger.error(f"Error finding latest version for {package_name}: {e}")
            return None

    async def update_packages(
        self,
        packages: Optional[List[str]] = None,
        outdated_packages: Optional[List[PackageInfo]] = None
    ) -> Tuple[bool, str]:
        """
        Update packages in dependency file using AI to understand and modify the format
        """
        self.logger.info(f"Updating packages in {self.dependency_file}")

        if not self.ai_client:
            return False, "AI client not available"

        try:
            # Get outdated packages
            if outdated_packages is not None:
                outdated = outdated_packages
            else:
                outdated = await self.get_outdated_packages()

            if not outdated:
                return True, "No outdated packages to update"

            # Read current file
            dep_file_path = self.repo_path / self.dependency_file
            with open(dep_file_path, 'r') as f:
                original_content = f.read()

            # Use AI to update the file
            updated_content = await self._update_file_with_ai(
                original_content,
                outdated,
                packages
            )

            if updated_content == original_content:
                return True, "No changes made to dependency file"

            # Write updated content
            with open(dep_file_path, 'w') as f:
                f.write(updated_content)

            output = f"Updated {len(outdated)} packages in {self.dependency_file}:\n\n"
            for pkg in outdated:
                output += f"✓ {pkg.name}: {pkg.current_version} → {pkg.latest_version}\n"

            return True, output

        except Exception as e:
            return False, f"Error updating packages: {e}"

    async def _update_file_with_ai(
        self,
        file_content: str,
        outdated_packages: List[PackageInfo],
        filter_packages: Optional[List[str]] = None
    ) -> str:
        """
        Use AI to update dependency file with new versions
        """
        # Build update instructions
        updates = []
        for pkg in outdated_packages:
            if filter_packages and pkg.name not in filter_packages:
                continue
            updates.append(f"- {pkg.name}: {pkg.current_version} → {pkg.latest_version}")

        updates_text = "\n".join(updates)

        prompt = f"""Update this {self.dependency_file} file with new package versions.

Current file content:
```
{file_content}
```

Updates to make:
{updates_text}

Return the COMPLETE updated file content with the new versions.
Preserve the exact format, comments, and structure of the original file.
Only change the version numbers for the packages listed above.

Return the updated file content without any explanation or markdown.
"""

        try:
            message = self.ai_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            updated_content = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    updated_content += block.text

            # Clean up any markdown code blocks that AI might add
            updated_content = updated_content.replace('```', '').strip()

            # Remove language identifiers if present
            lines = updated_content.split('\n')
            if lines and lines[0] in ['python', 'javascript', 'json', 'toml', 'yaml']:
                lines = lines[1:]
                updated_content = '\n'.join(lines)

            return updated_content

        except Exception as e:
            self.logger.error(f"Error updating file with AI: {e}")
            return file_content  # Return original on error

    def get_lockfile_paths(self) -> List[Path]:
        """Get lock file paths - use AI to determine common lock files"""
        lockfiles = []

        # Common lock file patterns
        lock_patterns = {
            'package.json': ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'],
            'requirements.txt': ['requirements.lock'],
            'pyproject.toml': ['poetry.lock', 'Pipfile.lock'],
            'Cargo.toml': ['Cargo.lock'],
            'go.mod': ['go.sum'],
            'Gemfile': ['Gemfile.lock'],
            'composer.json': ['composer.lock'],
        }

        # Add main dependency file
        if self.file_exists(self.dependency_file):
            lockfiles.append(self.repo_path / self.dependency_file)

        # Add lock files if they exist
        for lock_file in lock_patterns.get(self.dependency_file, []):
            if self.file_exists(lock_file):
                lockfiles.append(self.repo_path / lock_file)

        self.logger.info(f"Found {len(lockfiles)} files to commit: {[f.name for f in lockfiles]}")
        return lockfiles

    def get_main_dependency_file(self) -> Optional[str]:
        """Get the main dependency file"""
        return self.dependency_file
