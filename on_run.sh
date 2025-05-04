#!/bin/bash
# on_run.sh - Simple script to run Open Notebook CLI commands in the container
# Enhanced version that ensures dependencies are installed

CONTAINER_NAME="assistant-notebook-1"
CLI_PATH="/app/open_notebook_cli.py"

# Function to check if dependencies are installed
check_dependencies() {
  echo "Checking if required dependencies are installed..."
  
  # Test if loguru can be imported
  if ! docker exec $CONTAINER_NAME python -c "import loguru" 2>/dev/null; then
    echo "Installing missing dependencies..."
    # Install dependencies using pip
    docker exec $CONTAINER_NAME pip install loguru pydantic langchain langgraph typing_extensions humanize pyyaml
    echo "Dependencies installed."
  else
    echo "Dependencies already installed."
  fi
}

# Display help if no arguments provided
if [ $# -eq 0 ]; then
  echo "Usage: ./on_run.sh <command> [options]"
  echo "Example: ./on_run.sh list-notebooks"
  exit 1
fi

# Check and install dependencies before running command
check_dependencies

# Run the command in the container
echo "Running command: python $CLI_PATH $@"
docker exec -it "$CONTAINER_NAME" python "$CLI_PATH" "$@"
