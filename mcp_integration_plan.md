# Open Notebook MCP Server Integration Plan

## Overview

This document outlines our approach to extending the `lfnovo/open_notebook:latest` Docker image to embed a Model Context Protocol (MCP) server within the Open Notebook environment.

## Current Status (Updated)

1. We've created a new `Dockerfile.mcp` that extends `lfnovo/open_notebook:latest` and adds:
   - FastAPI and Uvicorn for the MCP server
   - Supervisor for managing multiple processes
   - CLI script for tool functionality
   - Configuration for conditionally starting the MCP server

2. We've added configuration files:
   - `supervisord.mcp.conf` for process management
   - `start_services.sh` as the container entrypoint

3. We've updated:
   - `docker-compose.yml` to use the new image with the MCP server enabled
   - `tool_registry.py` to support executing tools via CLI
   - `open_notebook_mcp/main.py` to properly integrate with the CLI

4. **Issues Addressed**:
   - Fixed Python path issues with PYTHONPATH environment variable
   - Updated supervisor configuration to run the MCP server properly
   - Ensured CLI script is properly included in the image
   - Improved error handling and logging

## Running the Integration

### Docker Build

```bash
docker build -t open_notebook_mcp:latest -f Dockerfile.mcp .
```

### Docker Run

With MCP server enabled:
```bash
docker run -p 8502:8502 -p 8001:8001 -e ENABLE_MCP_SERVER=true open_notebook_mcp:latest
```

With MCP server disabled:
```bash
docker run -p 8502:8502 open_notebook_mcp:latest
```

### Docker Compose

```bash
docker compose --profile multi up
```

## Configuration

The MCP server is controlled by the `ENABLE_MCP_SERVER` environment variable (true/false) and runs on the port specified by `MCP_SERVER_PORT` (default: 8001).

## Testing

Use the provided test script to validate the integration:

```bash
bash test_mcp_integration.sh
```

## Documentation

See the full integration details in the [MCP CLI Integration Documentation](/docs/MCP_CLI_INTEGRATION.md).
