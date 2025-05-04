#!/bin/bash
# on_run.sh - Complete solution for Open Notebook CLI
# This script ensures all required dependencies are installed

CONTAINER_NAME="assistant-notebook-1"
CLI_PATH="/app/open_notebook_cli.py"

# Function to check and install dependencies
install_dependencies() {
  echo "Installing all required dependencies..."
  
  # Core dependencies
  echo "Installing core dependencies..."
  docker exec $CONTAINER_NAME pip install --upgrade pip
  docker exec $CONTAINER_NAME pip install loguru pydantic langchain langgraph
  
  # Database dependencies
  echo "Installing database dependencies..."
  docker exec $CONTAINER_NAME pip install sblpy surrealdb
  
  # Additional dependencies (yaml, etc.)
  echo "Installing additional dependencies..."
  docker exec $CONTAINER_NAME pip install pyyaml typing_extensions humanize
  
  # Plugin dependencies (streamlit, podcastfy)
  echo "Installing plugin dependencies..."
  docker exec $CONTAINER_NAME pip install streamlit podcastfy
  
  echo "All dependencies installed!"
}

# Display help if no arguments provided
if [ $# -eq 0 ]; then
  echo "Usage: ./on_run.sh <command> [options]"
  echo "Example: ./on_run.sh list-notebooks"
  echo ""
  echo "Special commands:"
  echo "  install    - Install all dependencies"
  echo "  shell      - Open a shell in the container"
  exit 1
fi

# Handle special commands
if [ "$1" = "install" ]; then
  install_dependencies
  exit 0
fi

if [ "$1" = "shell" ]; then
  echo "Opening shell in container..."
  docker exec -it "$CONTAINER_NAME" bash
  exit 0
fi

# Always check for missing dependencies before running a command
if ! docker exec $CONTAINER_NAME python -c "import sblpy" &>/dev/null; then
  echo "Missing dependencies detected. Installing..."
  install_dependencies
fi

# Run the command in the container
echo "Running command: python $CLI_PATH $@"
docker exec -it "$CONTAINER_NAME" python "$CLI_PATH" "$@"
