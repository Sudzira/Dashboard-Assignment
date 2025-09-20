#!/usr/bin/env python3
"""
Production startup script for Railway deployment
Handles Neo4j Graph Visualization app startup with proper configuration
"""

import os
import sys
import logging
import signal
from app import Neo4jGraphApp

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

def get_port():
    """Get port from environment variable (set by Railway)"""
    port = int(os.environ.get("PORT", 5006))
    logger.info(f"Using port: {port}")
    return port

def get_host():
    """Get host - must be 0.0.0.0 for Railway"""
    return "0.0.0.0"

def validate_environment():
    """Validate required environment variables"""
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        elif var == "NEO4J_URI":
            logger.info(f"Neo4j URI configured: {value}")
        elif var == "NEO4J_USER":
            logger.info(f"Neo4j User: {value}")
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these environment variables in Railway dashboard:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        return False
    
    logger.info("Environment variables validated successfully")
    return True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main entry point for production deployment"""
    logger.info("=" * 50)
    logger.info("Starting Neo4j Graph Visualization Application")
    logger.info("=" * 50)
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Show environment info
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Environment: {os.environ.get('NODE_ENV', 'development')}")
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Exiting...")
        logger.error("Please check Railway environment variables in dashboard")
        sys.exit(1)
    
    # Get configuration
    port = get_port()
    host = get_host()
    
    logger.info(f"Starting server on {host}:{port}")
    
    # Create and configure app
    app = Neo4jGraphApp()
    
    try:
        # Run the server (don't show browser in production)
        logger.info("Initializing application components...")
        app.run_server(port=port, host=host, show_browser=False)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down server...")
    except Exception as e:
        logger.error(f"Unexpected error during startup: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        logger.info("Cleaning up resources...")
        try:
            app.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
