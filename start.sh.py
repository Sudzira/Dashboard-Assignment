#!/usr/bin/env python3
"""
Production startup script for Railway deployment
Handles Neo4j Graph Visualization app startup with proper configuration
"""

import os
import sys
import logging
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
    return int(os.environ.get("PORT", 5006))

def get_host():
    """Get host - must be 0.0.0.0 for Railway"""
    return "0.0.0.0"

def validate_environment():
    """Validate required environment variables"""
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    logger.info("Environment variables validated successfully")
    return True

def main():
    """Main entry point for production deployment"""
    logger.info("Starting Neo4j Graph Visualization Application")
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Exiting...")
        sys.exit(1)
    
    # Get configuration
    port = get_port()
    host = get_host()
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Neo4j URI: {os.environ.get('NEO4J_URI', 'Not set')}")
    logger.info(f"Neo4j User: {os.environ.get('NEO4J_USER', 'Not set')}")
    
    # Create and configure app
    app = Neo4jGraphApp()
    
    try:
        # Run the server
        app.run_server(port=port, host=host, show_browser=False)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Shutting down server...")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("Cleaning up resources...")
        app.cleanup()
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
