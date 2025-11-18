# AI Dependency Update Agent

An intelligent AI-powered backend application that automatically detects outdated packages in repositories, updates them, and creates pull requests with AI-generated documentation using Anthropic's Claude.

## Features

- **AI-Driven Package Manager Detection**: Uses AI to detect and work with ANY dependency file format without hardcoded logic
- **MCP Web Search Integration**: Real-time package version detection using Model Context Protocol (MCP) and web search
- **Intelligent Dependency Analysis**: Uses Anthropic's Claude AI to analyze updates and potential breaking changes
- **Automated Updates**: Updates packages to their latest versions with real-time version data
- **Pull Request Creation**: Automatically creates PRs with comprehensive, AI-generated descriptions
- **RESTful API**: Easy-to-use REST API for integration
- **Comprehensive Logging**: Detailed logs for debugging each step of the process
- **Job Tracking**: Real-time status updates and progress tracking

## Architecture

```
┌─────────────────┐
│   REST API      │
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator   │
│   Service       │
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────────┬──────────────┐
    ▼         ▼            ▼              ▼              ▼
┌────────┐ ┌──────┐ ┌──────────┐ ┌─────────────┐ ┌──────────┐
│  Git   │ │GitHub│ │Anthropic │ │  Generic    │ │   MCP    │
│Service │ │ API  │ │   AI     │ │  Package    │ │WebSearch │
│        │ │      │ │          │ │  Manager    │ │ (stdio)  │
└────────┘ └──────┘ └──────────┘ └──────┬──────┘ └──────────┘
                                        │
                                        ▼
                                ┌───────────────┐
                                │ open-websearch│
                                │  MCP Server   │
                                │  (Real-time   │
                                │ Web Search)   │
                                └───────────────┘
```

## Supported Package Managers

This application uses an **AI-driven Generic Package Manager** that can work with ANY dependency file format without hardcoded logic. It automatically detects and handles:

- **JavaScript/Node.js**: package.json (npm, yarn, pnpm)
- **Python**: requirements.txt, pyproject.toml, Pipfile, setup.py
- **Rust**: Cargo.toml
- **Ruby**: Gemfile
- **PHP**: composer.json
- **Go**: go.mod
- **Java**: pom.xml, build.gradle
- **And ANY other dependency file format** - the AI adapts automatically!

## Installation

### Prerequisites

- **Python 3.11+** - For running the FastAPI backend
- **Node.js 18+** and **npm 8+** - Required for MCP WebSearch server
- **Git** - For repository operations
- **Internet connection** - For MCP web search to fetch real-time package versions

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AiAgent
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Node.js installation** (required for MCP WebSearch):
   ```bash
   node --version  # Should be 18.0.0 or higher
   npm --version   # Should be 8.0.0 or higher
   ```

   If Node.js is not installed, download it from [nodejs.org](https://nodejs.org/)

5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```env
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   GITHUB_TOKEN=your_github_token_here
   ```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Yes | - |
| `ANTHROPIC_MODEL` | Claude model to use | No | `claude-3-5-sonnet-20241022` |
| `GITHUB_TOKEN` | GitHub personal access token | Yes | - |
| `APP_HOST` | Server host | No | `0.0.0.0` |
| `APP_PORT` | Server port | No | `8000` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `WORKSPACE_DIR` | Temporary workspace directory | No | `./workspace` |
| `DEFAULT_BRANCH_PREFIX` | Prefix for update branches | No | `dependency-updates` |

### Getting API Keys

**Anthropic API Key**:
1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Navigate to API Keys section
3. Create a new API key

**GitHub Token**:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)

## MCP Integration for Real-time Version Detection

This application uses the **Model Context Protocol (MCP)** with the **open-websearch** MCP server to fetch real-time package version information from the web.

### How It Works

1. **MCP Client**: The Python backend includes an MCP client (via the `mcp` package)
2. **MCP Server**: Connects to `open-websearch` MCP server via stdio protocol
3. **Web Search**: The MCP server performs real-time web searches across multiple search engines
4. **Version Extraction**: AI extracts the latest version from search results
5. **No API Keys**: The open-websearch server requires no API keys

### MCP Server Details

- **Server**: [open-websearch](https://github.com/Aas-ee/open-webSearch)
- **Protocol**: Model Context Protocol (stdio transport)
- **Installation**: Automatic via `npx open-websearch@latest`
- **Search Engines**: Bing, DuckDuckGo, Brave, and more (no keys required)
- **Site-specific queries**: Searches package registries (pypi.org, npmjs.com, crates.io, etc.)

### What Happens When You Run the Application

When checking for package updates, the system:

```
1. Python backend creates MCP client session
2. Spawns open-websearch MCP server (via npx)
3. Sends web_search request with query like "latest version fastapi site:pypi.org 2025"
4. MCP server fetches real-time search results from the web
5. Returns search results to Python backend
6. AI (Claude) extracts the latest version number from results
7. Validates the version is newer than current version
8. Returns updated version information
```

### No Additional Setup Required

The MCP server is automatically started when needed via `npx`, so no manual installation or configuration is required. Just ensure Node.js 18+ and npm 8+ are installed.

## Usage

### Starting the Server

```bash
python run.py
```

The server will start on `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### 1. Create Update Job

**POST** `/api/update`

Create a new dependency update job.

**Request Body**:
```json
{
  "repository_url": "https://github.com/owner/repo",
  "branch": "main",
  "create_pr": true
}
```

**Response**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Job created successfully. Use the job_id to check status."
}
```

#### 2. Get Job Status

**GET** `/api/jobs/{job_id}`

Get the current status of a job.

**Response**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "repository_url": "https://github.com/owner/repo",
  "package_manager": "npm",
  "outdated_packages": [
    {
      "name": "express",
      "current_version": "4.17.1",
      "latest_version": "4.18.2",
      "is_outdated": true
    }
  ],
  "updated_packages": [...],
  "pr_url": "https://github.com/owner/repo/pull/123",
  "error": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00",
  "logs": [
    "[2024-01-15T10:30:00] Cloning repository...",
    "[2024-01-15T10:30:15] Detected package manager: npm",
    "[2024-01-15T10:30:30] Found 5 outdated packages",
    "[2024-01-15T10:32:00] Packages updated successfully",
    "[2024-01-15T10:35:00] Pull request created"
  ]
}
```

#### 3. List All Jobs

**GET** `/api/jobs`

Get a list of all jobs.

#### 4. Delete Job

**DELETE** `/api/jobs/{job_id}`

Delete a job from the tracking system.

#### 5. Supported Package Managers

**GET** `/api/supported-package-managers`

Get a list of supported package managers.

#### 6. Health Check

**GET** `/health`

Check if the service is running.

### Example Usage with cURL

**Create an update job**:
```bash
curl -X POST "http://localhost:8000/api/update" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/your-username/your-repo",
    "create_pr": true
  }'
```

**Check job status**:
```bash
curl "http://localhost:8000/api/jobs/{job_id}"
```

### Example Usage with Python

```python
import requests
import time

# Create update job
response = requests.post(
    "http://localhost:8000/api/update",
    json={
        "repository_url": "https://github.com/your-username/your-repo",
        "create_pr": True
    }
)

job = response.json()
job_id = job["job_id"]

print(f"Job created: {job_id}")

# Poll for status
while True:
    response = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
    status = response.json()

    print(f"Status: {status['status']}")

    if status["status"] in ["completed", "failed"]:
        if status.get("pr_url"):
            print(f"PR created: {status['pr_url']}")
        break

    time.sleep(5)
```

## Workflow

1. **Repository Cloning**: The agent clones the specified repository
2. **AI-Powered Detection**: Uses Claude AI to detect the dependency file and package manager (works with ANY format)
3. **Dependency Parsing**: AI parses the dependency file to extract current packages and versions
4. **Real-time Version Check**:
   - Connects to open-websearch MCP server via stdio
   - Performs web search for each package (e.g., "latest version fastapi site:pypi.org 2025")
   - AI extracts latest version from real-time search results
   - Validates versions are newer than current
5. **AI Analysis**: Uses Claude to analyze potential breaking changes and risks
6. **Package Updates**: Updates packages to their latest versions
7. **Branch Creation**: Creates a new branch for the updates
8. **Commit Changes**: Commits the updated dependency files
9. **PR Description Generation**: Uses Claude AI to generate comprehensive PR description
10. **Pull Request Creation**: Creates a PR on GitHub with the AI-generated description

## Logging

The application provides comprehensive logging:

- **Console Logs**: Colored, formatted logs in the terminal
- **File Logs**: Detailed logs saved to `logs/ai_agent_YYYYMMDD.log`
- **Job Logs**: Per-job logs available via the API

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## Project Structure

```
AiAgent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── logger.py               # Logging setup
│   ├── models.py               # Pydantic models
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── git_service.py      # Git operations
│   │   ├── github_service.py   # GitHub API
│   │   ├── anthropic_agent.py  # AI agent
│   │   └── orchestrator.py     # Main workflow orchestrator
│   └── package_managers/
│       ├── __init__.py
│       ├── base.py             # Base package manager class
│       ├── npm.py              # npm implementation
│       ├── pip.py              # pip implementation
│       ├── cargo.py            # cargo implementation
│       └── detector.py         # Package manager detection
├── logs/                       # Log files
├── workspace/                  # Temporary workspace (git ignored)
├── .env                        # Environment variables (git ignored)
├── .env.example                # Environment template
├── .gitignore
├── requirements.txt            # Python dependencies
├── run.py                      # Entry point
└── README.md
```

## Error Handling

The application includes comprehensive error handling:

- Invalid repository URLs
- Authentication failures
- Package manager not supported
- Update failures
- PR creation failures

All errors are logged and returned via the API with appropriate HTTP status codes.

## Security Considerations

- **API Keys**: Never commit `.env` file to version control
- **GitHub Token**: Use tokens with minimal required permissions
- **Workspace**: Temporary repositories are cleaned up after processing
- **Input Validation**: All inputs are validated using Pydantic models

## Contributing

Contributions are welcome! Areas for improvement:

- Implement webhook support for automatic updates
- Add configuration for update policies (semver ranges, etc.)
- Support for monorepos with multiple package managers
- Improve MCP integration and add fallback mechanisms
- Add comprehensive test suite
- Performance optimizations for MCP web search
- Add support for private package registries

## License

MIT License

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with**:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Anthropic Claude](https://www.anthropic.com/) - AI-powered analysis and package detection
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Standard protocol for AI-tool integration
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Official Python MCP client
- [open-websearch](https://github.com/Aas-ee/open-webSearch) - MCP server for real-time web search
- [PyGithub](https://github.com/PyGithub/PyGithub) - GitHub API client
- [GitPython](https://gitpython.readthedocs.io/) - Git operations
