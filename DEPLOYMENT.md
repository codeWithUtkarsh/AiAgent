# Deployment Guide

This guide covers different deployment options for the AI Dependency Update Agent.

## Table of Contents

- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Considerations](#production-considerations)

## Local Deployment

### Prerequisites

- Python 3.11+
- Git
- npm, pip, cargo (depending on which package managers you want to support)

### Steps

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd AiAgent
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure environment**:
   Edit `.env` file and add your API keys:
   ```env
   ANTHROPIC_API_KEY=your_key_here
   GITHUB_TOKEN=your_token_here
   ```

3. **Run the application**:
   ```bash
   source venv/bin/activate
   python run.py
   ```

4. **Test the deployment**:
   ```bash
   python test_api.py
   ```

## Docker Deployment

### Using Docker

1. **Build the image**:
   ```bash
   docker build -t ai-dependency-agent .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e ANTHROPIC_API_KEY=your_key \
     -e GITHUB_TOKEN=your_token \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/workspace:/app/workspace \
     --name ai-agent \
     ai-dependency-agent
   ```

3. **View logs**:
   ```bash
   docker logs -f ai-agent
   ```

### Using Docker Compose

1. **Configure environment**:
   Create `.env` file with your API keys

2. **Start the service**:
   ```bash
   docker-compose up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f
   ```

4. **Stop the service**:
   ```bash
   docker-compose down
   ```

## Cloud Deployment

### AWS EC2

1. **Launch an EC2 instance** (Ubuntu 22.04 LTS recommended)

2. **SSH into the instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3.11-venv git
   ```

4. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd AiAgent
   chmod +x setup.sh
   ./setup.sh
   ```

5. **Configure environment variables**

6. **Run with systemd** (create `/etc/systemd/system/ai-agent.service`):
   ```ini
   [Unit]
   Description=AI Dependency Update Agent
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/AiAgent
   Environment="PATH=/home/ubuntu/AiAgent/venv/bin"
   ExecStart=/home/ubuntu/AiAgent/venv/bin/python run.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ai-agent
   sudo systemctl start ai-agent
   ```

### Google Cloud Run

1. **Build and push Docker image**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/ai-agent
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy ai-agent \
     --image gcr.io/PROJECT_ID/ai-agent \
     --platform managed \
     --region us-central1 \
     --set-env-vars ANTHROPIC_API_KEY=your_key,GITHUB_TOKEN=your_token
   ```

### Heroku

1. **Create Heroku app**:
   ```bash
   heroku create ai-dependency-agent
   ```

2. **Set environment variables**:
   ```bash
   heroku config:set ANTHROPIC_API_KEY=your_key
   heroku config:set GITHUB_TOKEN=your_token
   ```

3. **Create Procfile**:
   ```
   web: python run.py
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### DigitalOcean App Platform

1. **Create `app.yaml`**:
   ```yaml
   name: ai-dependency-agent
   services:
   - name: web
     github:
       repo: your-username/AiAgent
       branch: main
     build_command: pip install -r requirements.txt
     run_command: python run.py
     envs:
     - key: ANTHROPIC_API_KEY
       value: your_key
     - key: GITHUB_TOKEN
       value: your_token
     http_port: 8000
   ```

2. **Deploy via CLI or web interface**

## Production Considerations

### Security

1. **Use secrets management**:
   - AWS Secrets Manager
   - Google Cloud Secret Manager
   - HashiCorp Vault
   - Azure Key Vault

2. **API Authentication**:
   Add authentication middleware to protect endpoints

3. **Rate Limiting**:
   Implement rate limiting to prevent abuse

4. **HTTPS**:
   Always use HTTPS in production (use reverse proxy like Nginx)

### Monitoring

1. **Application Monitoring**:
   - Datadog
   - New Relic
   - Prometheus + Grafana

2. **Log Aggregation**:
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Splunk
   - CloudWatch (AWS)

3. **Alerts**:
   Set up alerts for:
   - Failed jobs
   - API errors
   - High memory/CPU usage

### Scalability

1. **Horizontal Scaling**:
   - Use load balancer
   - Deploy multiple instances
   - Use container orchestration (Kubernetes)

2. **Job Queue**:
   - Replace in-memory job storage with Redis or database
   - Use Celery for distributed task queue

3. **Database**:
   - Store job history in PostgreSQL or MongoDB
   - Cache results with Redis

### Performance

1. **Optimize cloning**:
   - Use shallow clones (already implemented)
   - Clean up workspace regularly

2. **Concurrency**:
   - Process multiple jobs in parallel
   - Use async/await effectively

3. **Caching**:
   - Cache package information
   - Cache GitHub API responses

### Reliability

1. **Error Handling**:
   - Implement retry logic
   - Graceful degradation
   - Circuit breakers

2. **Backups**:
   - Backup job data
   - Backup logs

3. **Health Checks**:
   - Implement deep health checks
   - Monitor external dependencies

### Example Production Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for long-running jobs
        proxy_read_timeout 600s;
    }
}
```

### Environment Variables for Production

```env
# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
GITHUB_TOKEN=your_github_token

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Workspace
WORKSPACE_DIR=/var/lib/ai-agent/workspace

# Production settings
WORKERS=4
MAX_JOBS=100
JOB_TIMEOUT=3600
```

## Monitoring Checklist

- [ ] Application logs are being collected
- [ ] Error tracking is set up
- [ ] Performance metrics are monitored
- [ ] Alerts are configured
- [ ] Health checks are in place
- [ ] Backup strategy is implemented
- [ ] Security scanning is enabled
- [ ] SSL/TLS certificates are valid

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   # Kill the process or use different port
   APP_PORT=8001 python run.py
   ```

2. **Git operations failing**:
   - Check GitHub token permissions
   - Ensure git is installed
   - Verify repository access

3. **Package manager not found**:
   - Install required package managers (npm, pip, cargo)
   - Check PATH environment variable

4. **Out of disk space**:
   - Clean up workspace directory
   - Implement automatic cleanup
   - Monitor disk usage

## Support

For deployment issues, please open an issue on GitHub.
