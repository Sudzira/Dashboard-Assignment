#!/bin/bash
# Railway startup script for Neo4j Graph Visualization

echo "Starting Neo4j Graph Visualization Application..."

# Check if required environment variables are set
if [ -z "$NEO4J_URI" ]; then
    echo "Error: NEO4J_URI environment variable is required"
    exit 1
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    echo "Error: NEO4J_PASSWORD environment variable is required"
    exit 1
fi

# Set default values
export NEO4J_USER=${NEO4J_USER:-neo4j}
export PORT=${PORT:-5006}
export MAX_NODES=${MAX_NODES:-1000}

echo "Configuration:"
echo "  - Neo4j URI: $NEO4J_URI"
echo "  - Neo4j User: $NEO4J_USER"
echo "  - Port: $PORT"
echo "  - Max Nodes: $MAX_NODES"

# Install dependencies if needed (Railway should handle this, but just in case)
if [ ! -d "venv" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start the application
echo "Starting Python application..."
exec python start.py