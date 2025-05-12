# Debug script for the MCP container issue
#!/bin/bash

# Create a debug script to diagnose the issue in the container
echo "Debugging Open Notebook MCP Integration Issues"
echo "=============================================="

# 1. Create a debugging Jupyter Notebook
cat > /Users/gregory/localcode/open-notebook/debug_mcp_integration.ipynb << EOF
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# MCP Integration Debugging\n",
    "\n",
    "This notebook helps to diagnose and fix issues with the MCP server integration."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Analysis of the Issue\n",
    "\n",
    "From the logs, we've identified two main issues:\n",
    "\n",
    "1. **Module Import Error**: The MCP server can't find the `open_notebook.tool_registry` module\n",
    "2. **Supervisor Configuration Error**: There's a mismatch between the intended supervisord configuration and what's being executed"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Fix for Module Import Error\n",
    "\n",
    "To fix the module import error, we need to ensure that the `open_notebook` package is properly installed in the container's Python environment."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Command to run in the container to check Python path\n",
    "python_path_check = '''\n",
    "import sys\n",
    "print(\"\\nPython Path:\")\n",
    "for path in sys.path:\n",
    "    print(f\"  {path}\")\n",
    "'''\n",
    "\n",
    "print(python_path_check)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Command to check installed packages\n",
    "package_check = '''\n",
    "import pkg_resources\n",
    "print(\"\\nInstalled Packages:\")\n",
    "for pkg in pkg_resources.working_set:\n",
    "    print(f\"  {pkg.project_name} {pkg.version}\")\n",
    "'''\n",
    "\n",
    "print(package_check)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Modified Dockerfile.mcp\n",
    "\n",
    "Here's an updated Dockerfile.mcp that should fix the module import issues:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "updated_dockerfile = '''\n",
    "# Extending the base open_notebook image with MCP server\n",
    "FROM lfnovo/open_notebook:latest\n",
    "\n",
    "# Set environment variable to control MCP server activation\n",
    "ENV ENABLE_MCP_SERVER=false \\\n",
    "    MCP_SERVER_PORT=8001 \\\n",
    "    PYTHONPATH=/app\n",
    "\n",
    "# Install system dependencies required for the MCP server\n",
    "RUN apt-get update && apt-get install -y \\\n",
    "    supervisor \\\n",
    "    curl \\\n",
    "    && rm -rf /var/lib/apt/lists/*\n",
    "\n",
    "# Create necessary directories\n",
    "WORKDIR /app\n",
    "\n",
    "# Copy CLI script for MCP server interaction\n",
    "COPY ./open_notebook_cli.py /app/open_notebook_cli.py\n",
    "RUN chmod +x /app/open_notebook_cli.py\n",
    "\n",
    "# Copy open_notebook package\n",
    "COPY ./open_notebook /app/open_notebook\n",
    "\n",
    "# Copy MCP server files\n",
    "COPY ./open_notebook_mcp /app/open_notebook_mcp\n",
    "\n",
    "# Install MCP server dependencies using uv\n",
    "RUN uv pip install fastapi \"uvicorn[standard]\" pydantic\n",
    "\n",
    "# Install the open_notebook package in development mode for CLI and MCP server access\n",
    "RUN cd /app && uv pip install -e .\n",
    "\n",
    "# Set up supervisord configuration\n",
    "COPY ./supervisord.mcp.conf /etc/supervisord.conf\n",
    "\n",
    "# Create a startup script to conditionally start services\n",
    "COPY ./start_services.sh /app/start_services.sh\n",
    "RUN chmod +x /app/start_services.sh\n",
    "\n",
    "# Expose ports for both services\n",
    "# 8502 - Open Notebook Streamlit app (already exposed in base image)\n",
    "# 8001 - MCP Server (new port to avoid conflict with SurrealDB which uses 8000)\n",
    "EXPOSE 8502 8001\n",
    "\n",
    "# Use the startup script as entrypoint\n",
    "ENTRYPOINT [\"/app/start_services.sh\"]\n",
    "'''\n",
    "\n",
    "print(updated_dockerfile)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. Fixed Supervisord Configuration\n",
    "\n",
    "Here's the updated supervisord.mcp.conf that should correctly start the MCP server:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "fixed_supervisord_conf = '''\n",
    "[supervisord]\n",
    "nodaemon=true\n",
    "logfile=/dev/stdout\n",
    "logfile_maxbytes=0\n",
    "pidfile=/tmp/supervisord.pid\n",
    "user=root\n",
    "\n",
    "[program:open_notebook]\n",
    "command=uv run streamlit run app_home.py\n",
    "stdout_logfile=/dev/stdout\n",
    "stdout_logfile_maxbytes=0\n",
    "stderr_logfile=/dev/stderr\n",
    "stderr_logfile_maxbytes=0\n",
    "autorestart=true\n",
    "priority=10\n",
    "\n",
    "[program:mcp_server]\n",
    "command=uv run uvicorn open_notebook_mcp.main:app --host 0.0.0.0 --port %(ENV_MCP_SERVER_PORT)s\n",
    "autostart=%(ENV_ENABLE_MCP_SERVER)s\n",
    "stdout_logfile=/dev/stdout\n",
    "stdout_logfile_maxbytes=0\n",
    "stderr_logfile=/dev/stderr\n",
    "stderr_logfile_maxbytes=0\n",
    "autorestart=true\n",
    "priority=20\n",
    "environment=PYTHONPATH=\"/app\"\n",
    "'''\n",
    "\n",
    "print(fixed_supervisord_conf)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 5. Steps to Fix the Issues\n",
    "\n",
    "1. Update the Dockerfile.mcp file\n",
    "2. Ensure the supervisord.mcp.conf file is correct\n",
    "3. Rebuild the Docker image\n",
    "4. Test the integration"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 6. Testing Commands\n",
    "\n",
    "After implementing the fixes, use these commands to test the integration:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "testing_commands = '''\n",
    "# Rebuild the image\n",
    "docker build -t open_notebook_mcp:latest -f Dockerfile.mcp .\n",
    "\n",
    "# Run the container\n",
    "docker run --rm -it -p 8502:8502 -p 8001:8001 -e ENABLE_MCP_SERVER=true open_notebook_mcp:latest\n",
    "\n",
    "# Connect to the container for debugging\n",
    "docker exec -it [CONTAINER_ID] /bin/bash\n",
    "\n",
    "# Inside the container, check Python path\n",
    "python -c \"import sys; print(sys.path)\"\n",
    "\n",
    "# Check if open_notebook module can be imported\n",
    "python -c \"import open_notebook; print(open_notebook.__file__)\"\n",
    "\n",
    "# Check if the tool_registry module can be imported\n",
    "python -c \"import open_notebook.tool_registry; print(open_notebook.tool_registry.__file__)\"\n",
    "'''\n",
    "\n",
    "print(testing_commands)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.9"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
EOF

# 2. Create a fix script
cat > /Users/gregory/localcode/open-notebook/fix_mcp_integration.sh << EOF
#!/bin/bash
# Fix script for Open Notebook MCP Integration

echo "Applying MCP Integration Fixes"
echo "============================="

# Fix 1: Update supervisord.mcp.conf
echo "Fixing supervisord.mcp.conf..."
cat > ./supervisord.mcp.conf << 'CONF'
[supervisord]
nodaemon=true
logfile=/dev/stdout
logfile_maxbytes=0
pidfile=/tmp/supervisord.pid
user=root

[program:open_notebook]
command=uv run streamlit run app_home.py
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autorestart=true
priority=10

[program:mcp_server]
command=uv run uvicorn open_notebook_mcp.main:app --host 0.0.0.0 --port %(ENV_MCP_SERVER_PORT)s
autostart=%(ENV_ENABLE_MCP_SERVER)s
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autorestart=true
priority=20
environment=PYTHONPATH="/app"
CONF
echo "supervisord.mcp.conf updated."

# Fix 2: Create a Python setup.py file for proper package installation
echo "Creating setup.py file..."
cat > ./setup.py << 'SETUP'
from setuptools import setup, find_packages

setup(
    name="open-notebook",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
)
SETUP
echo "setup.py created."

# Fix 3: Rebuild the Docker image
echo "Rebuilding Docker image..."
docker build -t open_notebook_mcp:latest -f Dockerfile.mcp .

echo "Fix applied. Test with:"
echo "docker run --rm -it -p 8502:8502 -p 8001:8001 -e ENABLE_MCP_SERVER=true open_notebook_mcp:latest"
EOF

chmod +x /Users/gregory/localcode/open-notebook/fix_mcp_integration.sh
echo "Debug tools created:"
echo "1. debug_mcp_integration.ipynb - Jupyter notebook for analyzing the issue"
echo "2. fix_mcp_integration.sh - Script to fix the integration issues"
echo
echo "To apply the fixes, run:"
echo "./fix_mcp_integration.sh"
