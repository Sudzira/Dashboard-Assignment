# Railway Deployment Setup for Neo4j Graph Visualization

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Neo4j Database**: Either Neo4j Aura Cloud or your own Neo4j instance

## Project Structure

Your project should have this structure:
```
neo4j-graph-viz/
├── app.py
├── connect_to_neo4j.py
├── fetch_graph_data.py
├── graph_plotting.py
├── search_function.py
├── filter_function.py
├── requirements.txt
├── Procfile
├── railway.toml
├── .env.example
└── README.md
```

## Step 1: Create Railway Configuration Files

### 1.1 Create Procfile
```
web: python app.py server $PORT
```

### 1.2 Create railway.toml
```toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[env]
PORT = "5006"
PYTHONPATH = "/app"
```

### 1.3 Create .env.example
```
NEO4J_URI=neo4j+s://your-neo4j-uri
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
PORT=5006
```

## Step 2: Prepare Your Application for Railway

### 2.1 Update app.py for Railway deployment

Add this to the top of your `app.py`:

```python
import os
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler

# Railway-specific configuration
def get_port():
    return int(os.environ.get("PORT", 5006))

def get_host():
    return "0.0.0.0"  # Required for Railway

# Update the run_server method in Neo4jGraphApp class:
def run_server(self, port: int = None, host: str = None, show_browser: bool = False):
    port = port or get_port()
    host = host or get_host()
    
    # ... rest of your server code
    
    server = Server({'/': app}, port=port, address=host)
```

### 2.2 Create a production-ready startup script

Create `start.py`:
```python
#!/usr/bin/env python3
"""
Production startup script for Railway deployment
"""
import os
import sys
from app import Neo4jGraphApp

def main():
    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 5006))
    
    print(f"Starting Neo4j Graph Visualization on port {port}")
    
    app = Neo4jGraphApp()
    try:
        app.run_server(port=port, host="0.0.0.0", show_browser=False)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        app.cleanup()

if __name__ == "__main__":
    main()
```

Update your Procfile:
```
web: python start.py
```

## Step 3: Deploy to Railway

### 3.1 Using Railway CLI

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login to Railway:
```bash
railway login
```

3. Initialize project:
```bash
railway init
```

4. Set environment variables:
```bash
railway variables set NEO4J_URI=your-neo4j-uri
railway variables set NEO4J_USER=neo4j
railway variables set NEO4J_PASSWORD=your-password
```

5. Deploy:
```bash
railway up
```

### 3.2 Using Railway Web Dashboard

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account and select your repository
5. Railway will automatically detect it's a Python project

### 3.3 Configure Environment Variables

In Railway dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add these variables:
   - `NEO4J_URI`: Your Neo4j connection string
   - `NEO4J_USER`: Neo4j username (usually 'neo4j')
   - `NEO4J_PASSWORD`: Your Neo4j password
   - `PORT`: Will be automatically set by Railway

## Step 4: Neo4j Database Options

### 4.1 Option 1: Neo4j Aura Cloud (Recommended)

1. Go to [neo4j.com/aura](https://neo4j.com/aura)
2. Create a free account
3. Create a new database instance
4. Download the connection details
5. Use the provided URI in your Railway environment variables

Example URI format:
```
neo4j+s://xxxxx.databases.neo4j.io:7687
```

### 4.2 Option 2: Deploy Neo4j on Railway

1. Create a new Railway service for Neo4j
2. Use this Docker image: `neo4j:latest`
3. Set environment variables:
   ```
   NEO4J_AUTH=neo4j/your-password
   NEO4J_PLUGINS=["apoc"]
   ```
4. Use internal Railway networking to connect

## Step 5: Troubleshooting Railway Deployment Issues

### 5.1 "Script start.sh not found" Error

If you encounter this error, Railway couldn't determine how to build your app. Try these solutions:

**Solution 1: Verify File Permissions**
Ensure `start.sh` is executable:
```bash
chmod +x start.sh
git add start.sh
git commit -m "Make start.sh executable"
git push
```

**Solution 2: Alternative Procfile Configurations**
Try different Procfile configurations:

```
# Option A: Direct Python execution
web: python start.py

# Option B: Shell script with permissions
web: chmod +x start.sh && ./start.sh

# Option C: Using bash explicitly
web: bash start.sh

# Option D: Heroku-style with PORT variable
web: python start.py
```

**Solution 3: Use Railway's Environment Variables for Startup**
In Railway dashboard, go to "Variables" and set:
- `RAILWAY_STATIC_URL`: `true`
- `PORT`: `5006`
- `START_COMMAND`: `python start.py`

**Solution 4: Manual Deploy Configuration**
In Railway dashboard:
1. Go to "Settings" → "Deploy"
2. Set "Build Command": `pip install -r requirements.txt`
3. Set "Start Command": `python start.py`

### 5.2 Python Version Issues

If Railway can't find Python or has version conflicts:

1. **Add runtime.txt** with specific Python version:
```
python-3.9.18
```

2. **Update nixpacks.toml** to specify Python version:
```toml
[variables]
PYTHON_VERSION = "3.9.18"
```

### 5.3 Build Process Issues

**Check Railway Logs:**
1. Go to Railway dashboard
2. Click on your project
3. Go to "Deployments" tab
4. Click on the failing deployment
5. Check "Build Logs" and "Deploy Logs"

**Common Build Fixes:**
```toml
# In railway.toml - force specific build process
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python start.py"
```

### 5.4 Force Railway to Recognize Python Project

Create a simple `setup.py` file:
```python
from setuptools import setup, find_packages

setup(
    name="neo4j-graph-viz",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        line.strip() 
        for line in open("requirements.txt").readlines()
    ],
    python_requires=">=3.8",
)
```

### 5.5 Alternative Deployment Methods

**Method 1: Railway CLI Force Deploy**
```bash
railway login
railway link  # Link to existing project
railway up --detach  # Force deploy
```

**Method 2: Direct Repository Deploy**
1. In Railway dashboard, create "New Project"
2. Choose "Deploy from GitHub repo"
3. Select your repository
4. Railway should auto-detect Python project

**Method 3: Docker Deployment**
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5006

CMD ["python", "start.py"]
```

Then in Railway, it will automatically detect and use Docker.

**Port Binding Error:**
- Ensure you're using `0.0.0.0` as host
- Use `$PORT` environment variable

**Neo4j Connection Issues:**
- Verify your Neo4j URI is correct
- Check if your Neo4j instance allows external connections
- Ensure credentials are correct

**Memory Issues:**
- Limit the amount of data loaded in production
- Use the `use_limited=True` option in your data fetcher

### 5.2 Performance Optimization

Add this to your app.py for production:

```python
def load_data_for_production(self):
    """Load optimized data for production deployment"""
    # Limit data size for better performance
    max_nodes = int(os.environ.get("MAX_NODES", 1000))
    
    return self.load_data(use_limited=True, limit=max_nodes)
```

### 5.3 Health Check Endpoint

Add a health check endpoint:

```python
from bokeh.models import Div

def create_health_check():
    """Simple health check endpoint"""
    return Div(text="<h1>App is running!</h1>")

# In your main app function, add:
if doc.session_context.request.path == "/health":
    doc.add_root(create_health_check())
    return
```

## Step 6: Monitor Your Application

### 6.1 Railway Logs

View logs in Railway dashboard:
1. Go to your project
2. Click on "Deployments"
3. Click on latest deployment
4. View logs in real-time

### 6.2 Error Monitoring

Add basic error logging:

```python
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Use logger throughout your app
logger.info("Application started")
logger.error("Error occurred: %s", str(e))
```

## Step 7: Custom Domain (Optional)

1. In Railway dashboard, go to "Settings"
2. Click "Domains"
3. Add your custom domain
4. Update DNS settings as instructed

## Environment Variables Summary

Required environment variables for Railway:

```bash
NEO4J_URI=neo4j+s://your-database.databases.neo4j.io:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password
PORT=5006  # Set automatically by Railway
MAX_NODES=1000  # Optional: Limit data for performance
DEBUG=false  # Optional: Set to true for development
```

## Security Considerations

1. **Never commit credentials** to your repository
2. **Use environment variables** for all sensitive data
3. **Enable HTTPS** (automatic on Railway)
4. **Restrict Neo4j access** to your Railway IP if possible
5. **Use strong passwords** for your Neo4j database

## Cost Optimization

Railway offers:
- **Free tier**: $5 credit monthly (sufficient for small apps)
- **Pro plan**: $20/month with more resources

To optimize costs:
- Limit data size in production
- Use efficient queries
- Monitor resource usage in Railway dashboard
- Scale down when not in use (if using Pro plan)

Your Neo4j Graph Visualization app should now be successfully deployed on Railway and accessible via the provided URL!
