# Troubleshooting Guide

Common issues and their solutions.

## Table of Contents

- [Authentication Errors](#authentication-errors)
- [Git/GitHub Errors](#gitgithub-errors)
- [Package Manager Errors](#package-manager-errors)
- [API Errors](#api-errors)
- [Performance Issues](#performance-issues)

## Authentication Errors

### Anthropic API Key Error

**Error**: `Error code: 401 - authentication_error: invalid x-api-key`

**Cause**: Invalid or missing Anthropic API key

**Solution**:
1. Check your `.env` file and ensure `ANTHROPIC_API_KEY` is set correctly
2. Get a valid API key from [Anthropic Console](https://console.anthropic.com/)
3. Make sure there are no extra spaces or quotes around the key
4. The key should start with `sk-ant-`

**Example `.env` configuration**:
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

**Note**: If Anthropic API key is not configured, the application will still work but will use fallback descriptions instead of AI-generated content.

### GitHub Token Error

**Error**: `GitHub API error` or `No access to repository`

**Cause**: Invalid or missing GitHub token, or insufficient permissions

**Solution**:
1. Verify your GitHub token in `.env`
2. Ensure the token has these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
3. Generate a new token at GitHub Settings → Developer settings → Personal access tokens

**Example `.env` configuration**:
```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
```

**Note**: If GitHub token is not configured, the application can still detect and update packages but won't be able to create pull requests.

## Git/GitHub Errors

### File Not Found Error

**Error**: `[Errno 2] No such file or directory: 'workspace/repo/package-lock.json'`

**Cause**: Lock file doesn't exist in the repository

**Solution**: This is now automatically handled. The application will skip non-existent files and only commit files that actually exist.

**What was fixed**:
- File existence check before committing
- Better logging of which files are being committed
- Graceful handling of missing lock files

### Push Failed Error

**Error**: `Git error while pushing` or `authentication failed`

**Cause**: Missing or invalid GitHub token

**Solution**:
1. Ensure GitHub token is set in `.env`
2. Check token permissions
3. If pushing to a private repository, ensure the token has `repo` scope

### Clone Failed Error

**Error**: `Git error while cloning` or `Repository not found`

**Cause**: Invalid repository URL or no access

**Solution**:
1. Verify the repository URL is correct
2. For private repositories, ensure GitHub token has access
3. Check if the repository exists
4. Use HTTPS URL format: `https://github.com/owner/repo`

## Package Manager Errors

### NPM Command Not Found

**Error**: `npm command not found`

**Cause**: npm is not installed or not in PATH

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install nodejs npm

# macOS
brew install node

# Verify installation
npm --version
```

### Pip Command Not Found

**Error**: `pip command not found`

**Cause**: pip is not installed

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install python3-pip

# macOS
brew install python

# Verify installation
pip --version
```

### Package Update Failed

**Error**: `npm update failed` or `Package update failed`

**Cause**: Various issues with package installation

**Solution**:
1. Check the error logs for specific package errors
2. Try updating packages manually in the repository
3. Check for network connectivity issues
4. Look for dependency conflicts in the output

### No Outdated Packages Found

**Issue**: Job completes but says no packages are outdated

**Cause**: All packages are already up to date, or check failed

**Solution**:
1. Manually check for updates in the repository
2. Review the job logs for any errors during the check phase
3. Ensure the package manager can run successfully

## API Errors

### Port Already in Use

**Error**: `Address already in use` or port 8000 is busy

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
APP_PORT=8001 python run.py
```

### Internal Server Error

**Error**: `500 Internal Server Error`

**Cause**: Various server-side errors

**Solution**:
1. Check the application logs in `logs/` directory
2. Look for error details in the console output
3. Verify all configuration is correct
4. Restart the server

### Job Not Found

**Error**: `404 Job not found`

**Cause**: Invalid job ID or job was deleted

**Solution**:
1. Verify the job ID is correct
2. List all jobs with `GET /api/jobs`
3. Note that jobs are stored in memory and will be lost on server restart

## Performance Issues

### Slow Package Detection

**Issue**: Detection phase takes too long

**Cause**: Large repository or slow network

**Solution**:
1. Use shallow clones (already implemented)
2. Check network connectivity
3. Consider caching dependencies

### Workspace Growing Large

**Issue**: `workspace/` directory using too much disk space

**Cause**: Repositories are not being cleaned up

**Solution**:
```bash
# Manually clean workspace
rm -rf workspace/*

# Or delete specific repository
rm -rf workspace/repo-name
```

**Automatic cleanup**: Repositories are automatically cleaned up after each job

### Out of Memory

**Issue**: Application crashes with out of memory

**Cause**: Too many concurrent jobs or large repositories

**Solution**:
1. Limit concurrent jobs
2. Increase available memory
3. Monitor resource usage
4. Implement job queue with limits

## Configuration Issues

### Environment Variables Not Loading

**Issue**: Settings not being picked up from `.env`

**Solution**:
1. Ensure `.env` file is in the project root
2. Check file format (no spaces around `=`)
3. Restart the application after changing `.env`
4. Verify file permissions

**Example correct format**:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
GITHUB_TOKEN=ghp_xxxxx
LOG_LEVEL=INFO
```

### Log Files Growing Large

**Issue**: Log files using too much disk space

**Solution**:
```bash
# Rotate logs manually
mv logs/ai_agent_*.log logs/archive/

# Or clean old logs
find logs/ -name "*.log" -mtime +30 -delete
```

## Debugging Tips

### Enable Debug Logging

Set `LOG_LEVEL=DEBUG` in `.env` for more detailed logs:

```env
LOG_LEVEL=DEBUG
```

### Check Application Logs

```bash
# Real-time logs
tail -f logs/ai_agent_*.log

# Search for errors
grep ERROR logs/ai_agent_*.log

# Search for specific job
grep "job-id" logs/ai_agent_*.log
```

### Test API Manually

```bash
# Test health
curl http://localhost:8000/health

# Test with verbose output
curl -v http://localhost:8000/api/jobs

# Check specific endpoint
python test_api.py
```

### Verify Dependencies

```bash
# Check Python version
python --version  # Should be 3.11+

# Verify packages
pip list | grep -E "fastapi|anthropic|gitpython"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Common Error Messages Explained

| Error | Meaning | Solution |
|-------|---------|----------|
| `invalid x-api-key` | Anthropic API key is wrong | Check API key in .env |
| `No such file or directory` | File doesn't exist | Now handled automatically |
| `authentication failed` | Git/GitHub auth issue | Check GitHub token |
| `npm command not found` | npm not installed | Install Node.js/npm |
| `Port already in use` | Port 8000 is busy | Kill process or use different port |
| `Job not found` | Invalid job ID | Check job ID or list all jobs |

## Getting Help

If you're still experiencing issues:

1. **Check logs**: Look in `logs/ai_agent_*.log` for detailed error messages
2. **Enable debug mode**: Set `LOG_LEVEL=DEBUG` in `.env`
3. **Test API**: Run `python test_api.py` to verify setup
4. **Check documentation**: Review README.md and API_DOCUMENTATION.md
5. **Open an issue**: Report bugs on GitHub with logs and error messages

## Quick Fixes

### Reset Everything

```bash
# Stop the server
# Clean workspace
rm -rf workspace/*

# Clean logs (optional)
rm -rf logs/*

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify configuration
cat .env

# Start fresh
python run.py
```

### Minimal Working Configuration

If you want to test without API keys:

```env
# Optional - will use fallbacks
ANTHROPIC_API_KEY=
GITHUB_TOKEN=

# Required
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
WORKSPACE_DIR=./workspace
```

The application will work with package detection and updates, but won't have AI-generated descriptions or PR creation.
