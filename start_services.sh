#!/bin/bash
# Start services based on the ENABLE_MCP_SERVER environment variable

# Display the current configuration
echo "Open Notebook with MCP Server Configuration:"
echo "----------------------------------------"
echo "ENABLE_MCP_SERVER: $ENABLE_MCP_SERVER"
echo "MCP_SERVER_PORT: $MCP_SERVER_PORT"
echo "PYTHONPATH: $PYTHONPATH"
echo "----------------------------------------"

# Run the debug script for diagnostics at startup
echo "Running startup diagnostics..."
python /app/debug_mcp_imports.py

# Set defaults
if [ "$ENABLE_MCP_SERVER" = "true" ]; then
    echo "Starting Open Notebook with MCP server enabled on port $MCP_SERVER_PORT"
    export ENABLE_MCP_SERVER=true
    
    # Make sure the MCP port is set properly
    if [ -z "$MCP_SERVER_PORT" ]; then
        echo "WARNING: MCP_SERVER_PORT not set, defaulting to 8001"
        export MCP_SERVER_PORT=8001
    fi
else
    echo "Starting Open Notebook with MCP server disabled"
    export ENABLE_MCP_SERVER=false
fi

# Ensure proper Python path for imports
if [[ ":$PYTHONPATH:" != *":/app:"* ]]; then
    echo "Adding /app to PYTHONPATH"
    export PYTHONPATH=/app:$PYTHONPATH
fi

# Output supervisord config for debugging
echo "Supervisord configuration:"
cat /etc/supervisor/conf.d/supervisord.conf

# Start supervisord to manage all services
echo "Starting supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
