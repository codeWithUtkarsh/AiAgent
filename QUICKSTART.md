# Quick Start Guide

Get the AI Dependency Update Agent up and running in 5 minutes!

## Prerequisites

- Python 3.11+
- Git installed
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- GitHub personal access token ([Create one here](https://github.com/settings/tokens))

## Setup (3 steps)

### 1. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create `.env` file from template
- Set up required directories

### 2. Configure API Keys

Edit the `.env` file:

```bash
nano .env  # or use your favorite editor
```

Add your keys:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
GITHUB_TOKEN=ghp_xxxxx
```

### 3. Start the Server

```bash
source venv/bin/activate
python run.py
```

You should see:
```
AI Dependency Update Agent Starting
Host: 0.0.0.0
Port: 8000
```

## Test the API

### Option 1: Using the Web UI

Open your browser and visit:
```
http://localhost:8000/docs
```

### Option 2: Using the Test Script

```bash
python test_api.py
```

### Option 3: Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Create an update job
curl -X POST http://localhost:8000/api/update \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/your-username/your-repo",
    "create_pr": false
  }'
```

## Your First Update

Here's a complete example:

```bash
# 1. Create update job
curl -X POST http://localhost:8000/api/update \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/expressjs/express",
    "create_pr": false
  }' | jq

# Output:
# {
#   "job_id": "abc-123-def",
#   "status": "pending",
#   "message": "Job created successfully..."
# }

# 2. Check job status
curl http://localhost:8000/api/jobs/abc-123-def | jq

# 3. Wait for completion and check again
# The job will go through: pending → cloning → detecting → analyzing → updating → completed
```

## What Happens During an Update?

1. **Cloning**: Repository is cloned to `workspace/`
2. **Detection**: Package manager is automatically detected (npm, pip, cargo, etc.)
3. **Analysis**: Claude AI analyzes outdated packages
4. **Updating**: Packages are updated to latest versions
5. **PR Creation**: If enabled, creates a PR with AI-generated description

## Common Commands

```bash
# Start server
python run.py

# Test API
python test_api.py

# View logs
tail -f logs/ai_agent_*.log

# Check supported package managers
curl http://localhost:8000/api/supported-package-managers

# List all jobs
curl http://localhost:8000/api/jobs
```

## Docker Quick Start

If you prefer Docker:

```bash
# 1. Build image
docker build -t ai-agent .

# 2. Run container
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
  --name ai-agent \
  ai-agent

# 3. View logs
docker logs -f ai-agent
```

Or with Docker Compose:

```bash
# 1. Create .env file with your keys
# 2. Start services
docker-compose up -d

# 3. View logs
docker-compose logs -f
```

## Troubleshooting

### Port 8000 already in use

```bash
# Use different port
APP_PORT=8001 python run.py
```

### API key errors

Make sure your `.env` file has valid keys:
```bash
cat .env | grep -E "ANTHROPIC|GITHUB"
```

### Package manager not found

Install the package manager you need:
```bash
# For npm projects
sudo apt install nodejs npm  # Ubuntu/Debian
brew install node            # macOS

# For pip projects (already have Python)

# For cargo projects
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Next Steps

- Read the full [README.md](README.md)
- Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for all endpoints
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment

## Need Help?

- Check the logs: `logs/ai_agent_*.log`
- Test with: `python test_api.py`
- Open an issue on GitHub

## Example Python Script

```python
import requests
import time

# Create job
response = requests.post(
    "http://localhost:8000/api/update",
    json={
        "repository_url": "https://github.com/your-username/your-repo",
        "create_pr": False  # Set to True to create PR
    }
)

job_id = response.json()["job_id"]
print(f"Job created: {job_id}")

# Monitor progress
while True:
    status = requests.get(f"http://localhost:8000/api/jobs/{job_id}").json()
    print(f"Status: {status['status']}")

    if status['status'] in ['completed', 'failed']:
        print(f"Final status: {status}")
        break

    time.sleep(5)
```

That's it! You're ready to automate dependency updates with AI!
