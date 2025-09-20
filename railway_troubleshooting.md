# Railway Deployment Troubleshooting Guide

## Issue: "pip: not found" during Railway build

This error occurs when Railway tries to use Docker instead of the Python buildpack. Here's how to fix it:

## Solution 1: Force Python Buildpack (Recommended)

### Step 1: Remove/Rename Dockerfile temporarily
```bash
# Rename Dockerfile to prevent Railway from using Docker
mv Dockerfile Dockerfile.backup

# Or add it to .dockerignore
echo "Dockerfile" >> .dockerignore
```

### Step 2: Ensure correct file structure
Make sure you have these files in your project root:
- `requirements.txt`
- `runtime.txt` (with Python version)
- `Procfile` (with simple Python command)
- `railway.toml` (forcing Python provider)

### Step 3: Commit and push changes
```bash
git add .
git commit -m "Fix Railway deployment - force Python buildpack"
git push
```

## Solution 2: Fix Docker Build (Alternative)

If you prefer using Docker, fix the Dockerfile:

```dockerfile
# Use official Python image with pip included
FROM python:3.9

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Start application
CMD ["python", "start.py"]
```

## Solution 3: Manual Railway Configuration

1. Go to Railway dashboard → Your project
2. Click "Settings" → "Build & Deploy"
3. Set these values:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start.py`
   - **Root Directory**: `/` (if deploying from root)

## Solution 4: Use Railway CLI with Force Deploy

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Set environment variables
railway variables set NEO4J_URI=your-neo4j-uri
railway variables set NEO4J_USER=neo4j  
railway variables set NEO4J_PASSWORD=your-password

# Force deploy with specific settings
railway up --detach
```

## Solution 5: Minimal Configuration Approach

Create the simplest possible configuration:

### Procfile
```
web: python start.py
```

### requirements.txt (minimal version)
```
neo4j==5.14.1
bokeh==3.3.0
networkx==3.1
pandas==2.1.3
numpy==1.24.3
tornado==6.3.3
```

### Remove these files temporarily:
- `Dockerfile`
- `railway.toml` 
- `nixpacks.toml`
- `start.sh`

Let Railway auto-detect everything.

## Debug Steps

### Check Railway Logs
1. Railway Dashboard → Your Project
2. "Deployments" tab
3. Click failing deployment
4. Check "Build Logs" and "Deploy Logs"

### Common Log Messages and Fixes

**"Could not detect a Nixpacks provider"**
- Add `runtime.txt` with `python-3.9.18`
- Ensure `requirements.txt` exists in root

**"ModuleNotFoundError"**
- Check all imports in your Python files
- Ensure all dependencies are in `requirements.txt`

**"Port binding error"**
- Update `start.py` to use `PORT` environment variable
- Ensure host is set to `0.0.0.0`

## Working Configuration Files

### Procfile
```
web: python start.py
```

### runtime.txt
```
python-3.9.18
```

### requirements.txt
```
neo4j==5.14.1
bokeh==3.3.0
networkx==3.1
pandas==2.1.3
numpy==1.24.3
tornado==6.3.3
python-dotenv==1.0.0
```

### railway.toml
```toml
[build]
builder = "NIXPACKS"

[build.nixpacksConfig]
providers = ["python"]

[deploy]
startCommand = "python start.py"

[env]
PYTHONPATH = "/app"
```

## Test Locally First

Before deploying to Railway, test locally:

```bash
# Set environment variables
export NEO4J_URI=your-neo4j-uri
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your-password
export PORT=5006

# Install dependencies
pip install -r requirements.txt

# Test the application
python start.py
```

## Alternative Deployment Platforms

If Railway continues to have issues, try:

1. **Heroku**: Similar to Railway but more mature
2. **Render**: Good Python support
3. **DigitalOcean App Platform**: Simple deployment
4. **Google Cloud Run**: Container-based deployment

## Quick Fix Checklist

- [ ] Remove or ignore Dockerfile
- [ ] Simple Procfile: `web: python start.py`
- [ ] Add runtime.txt with Python version
- [ ] Minimal requirements.txt
- [ ] Environment variables set in Railway dashboard
- [ ] Test locally before deploying
- [ ] Check Railway logs for specific errors

## Contact Support

If none of these solutions work:
1. Check Railway's [documentation](https://docs.railway.app)
2. Join Railway's [Discord community](https://discord.gg/railway)
3. Submit a support ticket through Railway dashboard

The key is to let Railway's Python buildpack handle the deployment automatically rather than fighting with Docker configuration.
