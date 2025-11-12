# AI Dependency Update Agent

An intelligent AI-powered backend application that automatically detects outdated packages in repositories, updates them, and creates pull requests with AI-generated documentation using Anthropic's Claude.

## Features

- **Automatic Package Manager Detection**: Supports npm, yarn, pnpm, pip, poetry, pipenv, cargo, and more
- **Intelligent Dependency Analysis**: Uses Anthropic's Claude AI to analyze updates and potential breaking changes
- **Automated Updates**: Updates packages to their latest versions
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
    ┌────┴────┬────────────┬──────────────┐
    ▼         ▼            ▼              ▼
┌────────┐ ┌──────┐ ┌──────────┐ ┌─────────────┐
│  Git   │ │GitHub│ │Anthropic │ │  Package    │
│Service │ │ API  │ │   AI     │ │  Managers   │
└────────┘ └──────┘ └──────────┘ └─────────────┘
```

## Supported Package Managers

- **JavaScript/Node.js**: npm, yarn, pnpm
- **Python**: pip, poetry, pipenv
- **Rust**: cargo
- **Java**: maven, gradle (coming soon)
- **PHP**: composer (coming soon)
- **Go**: go modules (coming soon)

## Installation

### Prerequisites

- Python 3.11+
- Git
- Package managers you want to support (npm, pip, cargo, etc.)

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

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
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
2. **Package Manager Detection**: Automatically detects the package manager (npm, pip, cargo, etc.)
3. **Dependency Analysis**: Checks for outdated packages
4. **AI Analysis**: Uses Claude to analyze potential breaking changes and risks
5. **Package Updates**: Updates packages to their latest versions
6. **Branch Creation**: Creates a new branch for the updates
7. **Commit Changes**: Commits the updated dependency files
8. **PR Description Generation**: Uses Claude AI to generate comprehensive PR description
9. **Pull Request Creation**: Creates a PR on GitHub with the AI-generated description

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

- Add support for more package managers (Maven, Gradle, Go modules)
- Implement webhook support for automatic updates
- Add configuration for update policies (semver ranges, etc.)
- Support for monorepos with multiple package managers
- Add tests

## License

MIT License

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with**:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Anthropic Claude](https://www.anthropic.com/) - AI-powered analysis
- [PyGithub](https://github.com/PyGithub/PyGithub) - GitHub API client
- [GitPython](https://gitpython.readthedocs.io/) - Git operations
