"""
MCP Client for package version checking using mcp-package-version server

This module provides a client interface to communicate with the mcp-package-version
MCP server via stdio transport. It supports checking package versions across various
package registries including npm, PyPI, Go, Maven, Cargo, etc.
"""

import asyncio
import json
import subprocess
from typing import Optional, Dict, Any, List
from app.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """Client for communicating with mcp-package-version MCP server"""

    def __init__(self, server_path: Optional[str] = None):
        """
        Initialize MCP client

        Args:
            server_path: Path to the mcp-package-version binary. If not provided,
                        will search common locations.
        """
        if server_path is None:
            # Try to find the binary in common locations
            import os
            import shutil

            # Try which first
            server_path = shutil.which("mcp-package-version")

            if not server_path:
                # Try common Go bin locations
                go_bin_paths = [
                    os.path.expanduser("~/go/bin/mcp-package-version"),
                    "/root/go/bin/mcp-package-version",
                    "/usr/local/go/bin/mcp-package-version",
                    "/bin/mcp-package-version",
                ]

                for path in go_bin_paths:
                    if os.path.exists(path):
                        server_path = path
                        break

            if not server_path:
                raise RuntimeError(
                    "mcp-package-version not found. Please install it with: "
                    "go install github.com/sammcj/mcp-package-version/v2@HEAD"
                )

        self.server_path = server_path
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    async def start(self):
        """Start the MCP server process"""
        try:
            logger.info(f"Starting MCP server: {self.server_path}")
            self.process = subprocess.Popen(
                [self.server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            logger.info("MCP server started successfully")

            # Initialize the connection
            await self._send_initialize()

        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise

    async def _send_initialize(self):
        """Send initialization request to MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    }
                },
                "clientInfo": {
                    "name": "ai-dependency-agent",
                    "version": "1.0.0"
                }
            }
        }

        response = await self._send_request(request)
        logger.debug(f"Initialize response: {response}")

        # Send initialized notification
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await self._send_notification(notification)

    def _next_request_id(self) -> int:
        """Generate next request ID"""
        self.request_id += 1
        return self.request_id

    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request and wait for response

        Args:
            request: JSON-RPC request object

        Returns:
            Response from the server
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP server not started")

        try:
            # Send request
            request_str = json.dumps(request) + "\n"
            logger.debug(f"Sending request: {request_str.strip()}")
            self.process.stdin.write(request_str)
            self.process.stdin.flush()

            # Read response
            response_str = self.process.stdout.readline()
            logger.debug(f"Received response: {response_str.strip()}")

            if not response_str:
                raise RuntimeError("No response from MCP server")

            response = json.loads(response_str)

            if "error" in response:
                error = response["error"]
                raise RuntimeError(f"MCP error: {error.get('message', 'Unknown error')}")

            return response

        except Exception as e:
            logger.error(f"Error sending request: {e}")
            raise

    async def _send_notification(self, notification: Dict[str, Any]):
        """
        Send a JSON-RPC notification (no response expected)

        Args:
            notification: JSON-RPC notification object
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP server not started")

        try:
            notification_str = json.dumps(notification) + "\n"
            logger.debug(f"Sending notification: {notification_str.strip()}")
            self.process.stdin.write(notification_str)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            raise

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server

        Returns:
            List of tool definitions
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/list"
        }

        response = await self._send_request(request)
        tools = response.get("result", {}).get("tools", [])
        logger.info(f"Available tools: {[t['name'] for t in tools]}")
        return tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = await self._send_request(request)
        return response.get("result", {})

    async def check_npm_package(self, package_name: str, current_version: str = "*") -> Optional[str]:
        """
        Check latest version of an npm package

        Args:
            package_name: Name of the npm package
            current_version: Current version (defaults to "*" to get latest)

        Returns:
            Latest version string or None if not found
        """
        try:
            logger.info(f"Checking npm package: {package_name}")
            result = await self.call_tool("check_npm_versions", {
                "dependencies": {
                    package_name: current_version
                }
            })

            # Parse the result - it's JSON within text
            content = result.get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
                # Parse the JSON response
                import json
                data = json.loads(text)
                if isinstance(data, list) and len(data) > 0:
                    for item in data:
                        if item.get("name") == package_name:
                            version = item.get("latestVersion")
                            if version:
                                logger.info(f"Found npm package {package_name} version: {version}")
                                return version

            logger.warning(f"Could not find version for npm package: {package_name}")
            return None

        except Exception as e:
            logger.error(f"Error checking npm package {package_name}: {e}")
            return None

    async def check_pypi_package(self, package_name: str, current_version: str = "") -> Optional[str]:
        """
        Check latest version of a PyPI package

        Args:
            package_name: Name of the PyPI package
            current_version: Current version (optional)

        Returns:
            Latest version string or None if not found
        """
        try:
            logger.info(f"Checking PyPI package: {package_name}")
            # Format: package or package==version
            requirement = f"{package_name}=={current_version}" if current_version else package_name

            result = await self.call_tool("check_python_versions", {
                "requirements": [requirement]
            })

            # Parse the result - it's JSON within text
            content = result.get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
                # Parse the JSON response
                import json
                data = json.loads(text)
                if isinstance(data, list) and len(data) > 0:
                    for item in data:
                        if item.get("name") == package_name:
                            version = item.get("latestVersion")
                            if version:
                                logger.info(f"Found PyPI package {package_name} version: {version}")
                                return version

            logger.warning(f"Could not find version for PyPI package: {package_name}")
            return None

        except Exception as e:
            logger.error(f"Error checking PyPI package {package_name}: {e}")
            return None

    async def check_go_package(self, package_name: str, current_version: str = "v0.0.0") -> Optional[str]:
        """
        Check latest version of a Go package

        Args:
            package_name: Full Go package name (e.g., github.com/gin-gonic/gin)
            current_version: Current version (defaults to v0.0.0)

        Returns:
            Latest version string (without 'v' prefix) or None if not found
        """
        try:
            logger.info(f"Checking Go package: {package_name}")
            result = await self.call_tool("check_go_versions", {
                "dependencies": {
                    package_name: current_version
                }
            })

            # Parse the result - it's JSON within text
            content = result.get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
                # Parse the JSON response
                import json
                data = json.loads(text)
                if isinstance(data, list) and len(data) > 0:
                    for item in data:
                        if item.get("name") == package_name:
                            version = item.get("latestVersion", "")
                            # Strip 'v' prefix if present
                            version = version.lstrip('v')
                            if version:
                                logger.info(f"Found Go package {package_name} version: {version}")
                                return version

            logger.warning(f"Could not find version for Go package: {package_name}")
            return None

        except Exception as e:
            logger.error(f"Error checking Go package {package_name}: {e}")
            return None

    async def check_cargo_package(self, package_name: str) -> Optional[str]:
        """
        Check latest version of a Cargo (Rust) package

        Note: The mcp-package-version server does not currently support Cargo/Rust packages.
        This method will return None.

        Args:
            package_name: Name of the Cargo package

        Returns:
            Latest version string or None if not found
        """
        logger.warning(f"Cargo package checking not supported by MCP server: {package_name}")
        # Cargo is not currently supported by mcp-package-version
        # Could fall back to crates.io API here if needed
        return None

    async def close(self):
        """Close the MCP server process"""
        if self.process:
            logger.info("Closing MCP server")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("MCP server did not terminate, killing it")
                self.process.kill()
            finally:
                self.process = None

    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()


# Singleton instance for reuse
_mcp_client: Optional[MCPClient] = None


async def get_mcp_client() -> MCPClient:
    """
    Get or create the singleton MCP client instance

    Returns:
        MCP client instance
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
        await _mcp_client.start()
    return _mcp_client


async def close_mcp_client():
    """Close the singleton MCP client instance"""
    global _mcp_client
    if _mcp_client:
        await _mcp_client.close()
        _mcp_client = None
