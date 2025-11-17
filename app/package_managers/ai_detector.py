import os
from pathlib import Path
from typing import Optional, Dict, List
from app.logger import get_logger
from anthropic import Anthropic

logger = get_logger(__name__)


class AIPackageManagerDetector:
    """
    AI-powered package manager detector using Claude to analyze repository structure
    and intelligently identify the package manager and project type.
    """

    def __init__(self, anthropic_api_key: Optional[str]):
        self.logger = logger
        self.client = None
        self.ai_enabled = False

        if anthropic_api_key and anthropic_api_key != "your_anthropic_api_key_here":
            try:
                self.client = Anthropic(api_key=anthropic_api_key)
                self.ai_enabled = True
                self.logger.info("AI-powered package manager detection enabled")
            except Exception as e:
                self.logger.error(f"Failed to initialize AI detector: {e}")

    def scan_repository_structure(self, repo_path: Path, max_depth: int = 2) -> Dict[str, any]:
        """
        Scan repository structure to gather information for AI analysis

        Args:
            repo_path: Path to repository
            max_depth: Maximum directory depth to scan

        Returns:
            Dictionary containing repository structure information
        """
        structure = {
            "root_files": [],
            "directories": [],
            "file_extensions": set(),
            "config_files": [],
            "build_files": [],
            "dependency_files": []
        }

        # Known dependency/config file patterns
        dependency_patterns = [
            'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
            'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock',
            'Cargo.toml', 'Cargo.lock',
            'pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle',
            'composer.json', 'composer.lock',
            'go.mod', 'go.sum',
            'Gemfile', 'Gemfile.lock',
            'mix.exs', 'mix.lock',
            'Package.swift',
            'pubspec.yaml',
            'build.sbt'
        ]

        try:
            # Scan root directory
            for item in repo_path.iterdir():
                if item.is_file():
                    filename = item.name
                    structure["root_files"].append(filename)

                    # Track file extensions
                    if item.suffix:
                        structure["file_extensions"].add(item.suffix)

                    # Identify dependency files
                    if filename in dependency_patterns:
                        structure["dependency_files"].append(filename)

                    # Identify config/build files
                    if any(pattern in filename.lower() for pattern in ['config', 'build', 'make', 'cmake']):
                        structure["config_files"].append(filename)

                elif item.is_dir() and not item.name.startswith('.'):
                    structure["directories"].append(item.name)

            # Convert set to list for JSON serialization
            structure["file_extensions"] = list(structure["file_extensions"])

            self.logger.info(f"Scanned repository: {len(structure['root_files'])} files, {len(structure['directories'])} directories")
            self.logger.info(f"Found dependency files: {structure['dependency_files']}")

        except Exception as e:
            self.logger.error(f"Error scanning repository: {e}")

        return structure

    async def detect_with_ai(self, repo_path: Path) -> Optional[Dict[str, str]]:
        """
        Use AI to detect package manager by analyzing repository structure

        Args:
            repo_path: Path to repository

        Returns:
            Dictionary with 'package_manager' and 'confidence' or None
        """
        if not self.ai_enabled or not self.client:
            self.logger.warning("AI detection not available, falling back to rule-based detection")
            return None

        # Scan repository structure
        structure = self.scan_repository_structure(repo_path)

        if not structure["dependency_files"] and not structure["root_files"]:
            self.logger.warning("No files found in repository for AI analysis")
            return None

        # Prepare prompt for Claude
        prompt = f"""Analyze this repository structure and identify the PRIMARY dependency file where all dependencies are listed.

Repository Structure:
- Root files: {', '.join(structure['root_files'][:30])}
- Directories: {', '.join(structure['directories'][:20])}
- File extensions: {', '.join(structure['file_extensions'][:20])}
- Dependency files found: {', '.join(structure['dependency_files'])}

Your task is to identify the MAIN file that contains the dependency list for this repository.

Examples of dependency files for different technologies:
- JavaScript/Node.js: package.json
- Python: requirements.txt, pyproject.toml, Pipfile
- Rust: Cargo.toml
- Go: go.mod
- Java: pom.xml, build.gradle
- PHP: composer.json
- Ruby: Gemfile
- .NET: *.csproj, packages.config
- Dart/Flutter: pubspec.yaml
- Swift: Package.swift

Based on the repository structure above, determine:
1. The PRIMARY dependency file name (the exact filename like "package.json", "requirements.txt", etc.)
2. The package manager used with this file
3. Your confidence level (high/medium/low)
4. The programming language

Respond in this exact format:
DEPENDENCY_FILE: <exact_filename>
PACKAGE_MANAGER: <package_manager_name>
CONFIDENCE: <high/medium/low>
LANGUAGE: <programming_language>
REASONING: <brief explanation>

Important: Focus on identifying the MAIN dependency file, not lock files."""

        try:
            self.logger.info("Analyzing repository with AI...")

            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract response
            response_text = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            self.logger.info(f"AI Analysis Response:\n{response_text}")

            # Parse response
            result = self._parse_ai_response(response_text)

            if result:
                self.logger.info(f"AI detected: {result['package_manager']} (confidence: {result['confidence']})")
                return result

        except Exception as e:
            self.logger.error(f"Error in AI detection: {e}")

        return None

    def _parse_ai_response(self, response: str) -> Optional[Dict[str, str]]:
        """Parse Claude's response into structured data"""
        try:
            lines = response.strip().split('\n')
            result = {}

            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace('_', '').replace('-', '')
                    value = value.strip()

                    if 'dependency' in key and 'file' in key:
                        result['dependency_file'] = value
                    elif 'package' in key or 'manager' in key:
                        result['package_manager'] = value.lower()
                    elif 'confidence' in key:
                        result['confidence'] = value.lower()
                    elif 'language' in key:
                        result['language'] = value
                    elif 'framework' in key:
                        result['framework'] = value
                    elif 'reasoning' in key:
                        result['reasoning'] = value

            # Must have dependency_file to be valid
            if 'dependency_file' in result:
                return result

        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")

        return None
