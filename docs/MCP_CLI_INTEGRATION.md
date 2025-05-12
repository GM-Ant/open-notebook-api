# MCP Server and CLI Integration Documentation

## Overview

This document describes how the Model Context Protocol (MCP) server integrates with the Open Notebook CLI to provide function-calling capabilities for the notebook environment.

## Components

### 1. MCP Server (`/app/open_notebook_mcp/main.py`)

The MCP server is a FastAPI application that:
- Exposes APIs for tool discovery and execution
- Loads tool schemas from the CLI
- Provides health checks and diagnostics
- Executes tool functions via the CLI

### 2. CLI (`/app/open_notebook_cli.py`)

The CLI script:
- Provides command-line interface to Open Notebook functionalities
- Defines commands for notebooks, sources, notes, transformations, etc.
- Is used by the MCP server to execute functions

### 3. Tool Registry (`/app/open_notebook/tool_registry.py`)

The tool registry:
- Maintains a registry of available tool schemas
- Provides lookup capabilities
- Executes tools using the CLI

### 4. Tool Reflector (`/app/open_notebook/tool_reflector.py`)

The tool reflector:
- Inspects the CLI and generates OpenAI-compatible tool schemas
- Converts CLI commands to function-calling schemas

## Integration Flow

1. The MCP server starts up and uses the Tool Reflector to inspect CLI commands
2. Tool schemas are loaded into the Tool Registry
3. Client applications can:
   - Discover available tools via `/tools` endpoint
   - Execute tools via `/execute/{tool_name}` endpoint, providing parameters as JSON
4. The Tool Registry executes commands by invoking the CLI script with appropriate arguments
5. Results are returned to the client

## Configuration

The MCP server can be enabled or disabled via the `ENABLE_MCP_SERVER` environment variable:
- `ENABLE_MCP_SERVER=true`: Enables the MCP server
- `ENABLE_MCP_SERVER=false`: Disables the MCP server (default)

The port can be configured via the `MCP_SERVER_PORT` environment variable (default: 8001).

## Building and Running

```bash
# Build the Docker image
docker build -t open_notebook_mcp:latest -f Dockerfile.mcp .

# Run with MCP server enabled
docker run -p 8502:8502 -p 8001:8001 -e ENABLE_MCP_SERVER=true open_notebook_mcp:latest

# Run with MCP server disabled
docker run -p 8502:8502 open_notebook_mcp:latest
```

## Testing

Use the provided test script to validate the integration:

```bash
bash test_mcp_integration.sh
```

This script tests:
1. MCP server activation when enabled
2. MCP server deactivation when disabled
3. Notebook functionality with MCP server enabled
4. CLI integration through the MCP server
