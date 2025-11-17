# API Documentation

Complete API reference for the AI Dependency Update Agent.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. The GitHub and Anthropic API keys are configured server-side via environment variables.

## Response Format

All responses are in JSON format.

### Success Response

```json
{
  "field1": "value1",
  "field2": "value2"
}
```

### Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Endpoints

### 1. Health Check

Check if the service is running.

**Endpoint**: `GET /health`

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "service": "AI Dependency Update Agent"
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

---

### 2. Create Update Job

Create a new dependency update job.

**Endpoint**: `POST /api/update`

**Request Body**:

```json
{
  "repository_url": "string (required)",
  "branch": "string (optional)",
  "create_pr": "boolean (optional, default: true)"
}
```

**Fields**:
- `repository_url` (required): GitHub repository URL
  - Format: `https://github.com/owner/repo`
  - Example: `https://github.com/facebook/react`
- `branch` (optional): Target branch name
  - If not specified, uses repository's default branch
  - Example: `main`, `develop`
- `create_pr` (optional): Whether to create a pull request
  - Default: `true`
  - Set to `false` to only update locally without creating PR

**Response**: `200 OK`

```json
{
  "job_id": "string",
  "status": "pending",
  "message": "Job created successfully. Use the job_id to check status."
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/update" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/owner/repo",
    "branch": "main",
    "create_pr": true
  }'
```

**Error Responses**:
- `500 Internal Server Error`: Failed to create job

---

### 3. Get Job Status

Retrieve the current status and details of a job.

**Endpoint**: `GET /api/jobs/{job_id}`

**Path Parameters**:
- `job_id` (required): Job ID returned from create update job

**Response**: `200 OK`

```json
{
  "job_id": "string",
  "status": "string",
  "repository_url": "string",
  "package_manager": "string | null",
  "outdated_packages": [
    {
      "name": "string",
      "current_version": "string",
      "latest_version": "string",
      "is_outdated": true
    }
  ],
  "updated_packages": [
    {
      "name": "string",
      "current_version": "string",
      "latest_version": "string",
      "is_outdated": true
    }
  ],
  "pr_url": "string | null",
  "error": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "logs": ["string"]
}
```

**Status Values**:
- `pending`: Job created, waiting to start
- `cloning`: Cloning repository
- `detecting`: Detecting package manager
- `analyzing`: Analyzing dependencies
- `updating`: Updating packages
- `creating_pr`: Creating pull request
- `completed`: Job completed successfully
- `failed`: Job failed

**Example**:
```bash
curl http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000
```

**Error Responses**:
- `404 Not Found`: Job not found

---

### 4. List All Jobs

Get a list of all jobs.

**Endpoint**: `GET /api/jobs`

**Response**: `200 OK`

```json
[
  {
    "job_id": "string",
    "status": "string",
    "repository_url": "string",
    "package_manager": "string | null",
    "outdated_packages": [],
    "updated_packages": [],
    "pr_url": "string | null",
    "error": "string | null",
    "created_at": "datetime",
    "updated_at": "datetime",
    "logs": []
  }
]
```

**Example**:
```bash
curl http://localhost:8000/api/jobs
```

---

### 5. Delete Job

Delete a job from the tracking system.

**Endpoint**: `DELETE /api/jobs/{job_id}`

**Path Parameters**:
- `job_id` (required): Job ID to delete

**Response**: `200 OK`

```json
{
  "message": "Job {job_id} deleted successfully"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000
```

**Error Responses**:
- `404 Not Found`: Job not found

---

### 6. Get Supported Package Managers

Get a list of supported package managers.

**Endpoint**: `GET /api/supported-package-managers`

**Response**: `200 OK`

```json
{
  "supported_package_managers": [
    "npm",
    "yarn",
    "pnpm",
    "pip",
    "poetry",
    "pipenv",
    "cargo",
    "maven",
    "gradle",
    "composer",
    "go"
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/supported-package-managers
```

---

## Data Models

### UpdateRequest

```json
{
  "repository_url": "string (required)",
  "branch": "string (optional)",
  "create_pr": "boolean (optional)"
}
```

### UpdateResponse

```json
{
  "job_id": "string",
  "status": "string",
  "message": "string"
}
```

### JobStatusResponse

```json
{
  "job_id": "string",
  "status": "string",
  "repository_url": "string",
  "package_manager": "string | null",
  "outdated_packages": [PackageInfo],
  "updated_packages": [PackageInfo],
  "pr_url": "string | null",
  "error": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "logs": ["string"]
}
```

### PackageInfo

```json
{
  "name": "string",
  "current_version": "string",
  "latest_version": "string",
  "is_outdated": "boolean"
}
```

---

## Usage Examples

### Python

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# Create update job
response = requests.post(
    f"{BASE_URL}/api/update",
    json={
        "repository_url": "https://github.com/owner/repo",
        "create_pr": True
    }
)
job = response.json()
job_id = job["job_id"]

# Poll for completion
while True:
    response = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
    status = response.json()

    print(f"Status: {status['status']}")
    print(f"Logs: {status['logs'][-1] if status['logs'] else 'No logs yet'}")

    if status["status"] in ["completed", "failed"]:
        if status.get("pr_url"):
            print(f"PR created: {status['pr_url']}")
        if status.get("error"):
            print(f"Error: {status['error']}")
        break

    time.sleep(5)
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function updateDependencies(repoUrl) {
  // Create job
  const { data: job } = await axios.post(`${BASE_URL}/api/update`, {
    repository_url: repoUrl,
    create_pr: true
  });

  console.log(`Job created: ${job.job_id}`);

  // Poll for completion
  while (true) {
    const { data: status } = await axios.get(`${BASE_URL}/api/jobs/${job.job_id}`);

    console.log(`Status: ${status.status}`);

    if (status.status === 'completed' || status.status === 'failed') {
      if (status.pr_url) {
        console.log(`PR created: ${status.pr_url}`);
      }
      if (status.error) {
        console.error(`Error: ${status.error}`);
      }
      break;
    }

    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

updateDependencies('https://github.com/owner/repo');
```

### cURL

```bash
#!/bin/bash

# Create job
JOB_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/update" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/owner/repo",
    "create_pr": true
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')

echo "Job created: $JOB_ID"

# Poll for status
while true; do
  STATUS_RESPONSE=$(curl -s "http://localhost:8000/api/jobs/$JOB_ID")
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')

  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    echo $STATUS_RESPONSE | jq '.'
    break
  fi

  sleep 5
done
```

---

## Rate Limiting

Currently, there are no rate limits. However, consider implementing rate limiting in production environments.

## Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Interactive Documentation

For interactive API documentation with try-it-out functionality:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
