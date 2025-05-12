#!/bin/bash
# Build and run the Open Notebook MCP server image

# Set environment variables and defaults
ENABLE_MCP=${1:-true}
PORT=${2:-8001}

# Display header
echo "=========================================="
echo "Open Notebook MCP Server Build & Run Tool"
echo "=========================================="
echo "MCP Server Enabled: $ENABLE_MCP"
echo "MCP Server Port: $PORT"
echo "=========================================="

# Build the Docker image
echo "Building Docker image..."
docker build -t open_notebook_mcp:latest -f Dockerfile.mcp .

if [ $? -ne 0 ]; then
    echo "Error building Docker image. Exiting."
    exit 1
fi

echo "Image built successfully."

# Run the Docker container
echo "Starting container with MCP server $([[ $ENABLE_MCP == "true" ]] && echo "enabled" || echo "disabled")..."
docker run --rm -it \
    -p 8502:8502 \
    -p $PORT:$PORT \
    -e ENABLE_MCP_SERVER=$ENABLE_MCP \
    -e MCP_SERVER_PORT=$PORT \
    -v $(pwd)/notebook_data:/app/data \
    --name open_notebook_mcp_test \
    open_notebook_mcp:latest

echo "Container stopped."
