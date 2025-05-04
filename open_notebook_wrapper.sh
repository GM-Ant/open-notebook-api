#!/bin/bash
# open_notebook_wrapper.sh
#
# A wrapper script for interacting with Open Notebook CLI from outside the Docker container.
# This script forwards commands to the Open Notebook CLI running inside the container.
#
# Usage:
#   ./open_notebook_wrapper.sh <command> [options]
#
# Example:
#   ./open_notebook_wrapper.sh list-notebooks
#   ./open_notebook_wrapper.sh create-notebook "My Research" "Notes about my research"
#   ./open_notebook_wrapper.sh add-text-source notebook:abc123 "Title" "Content"
#
# Run ./open_notebook_wrapper.sh --help for a list of available commands.

set -e  # Exit on error

# Container name for the Open Notebook instance
CONTAINER_NAME="assistant-notebook-1"
CLI_PATH="open_notebook_cli.py"

# Function to check if container is running
check_container() {
  if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Error: Container '$CONTAINER_NAME' is not running"
    echo "Please make sure the Open Notebook Docker container is started"
    exit 1
  fi
}

# Function to display usage information
show_usage() {
  echo "Open Notebook CLI Wrapper"
  echo ""
  echo "Usage:"
  echo "  ./open_notebook_wrapper.sh <command> [options]"
  echo ""
  echo "Examples:"
  echo "  ./open_notebook_wrapper.sh list-notebooks"
  echo "  ./open_notebook_wrapper.sh create-notebook \"My Research\" \"Description\""
  echo "  ./open_notebook_wrapper.sh add-url-source notebook:abc123 https://example.com"
  echo ""
  echo "For more information, use:"
  echo "  ./open_notebook_wrapper.sh --help"
}

# Show help message for available commands
show_help() {
  docker exec -it "$CONTAINER_NAME" python "$CLI_PATH" --help
}

# Check if container is running
check_container

# If no arguments are provided, show usage
if [ $# -eq 0 ]; then
  show_usage
  exit 0
fi

# Handle special flags
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  show_help
  exit 0
fi

# Special case for shell access to the container
if [ "$1" == "shell" ]; then
  echo "Entering shell in container $CONTAINER_NAME..."
  docker exec -it "$CONTAINER_NAME" bash
  exit 0
fi

# Escape special characters in arguments and build the command to run inside the container
args=()
for arg in "$@"; do
  # Properly escape quotes and special characters for passing to docker exec
  escaped_arg=$(printf "%q" "$arg")
  args+=("$escaped_arg")
done

# Combine arguments into a single string to pass to the container
command_str=$(printf "%s " "${args[@]}")

# Run the command inside the container
echo "Executing: python $CLI_PATH $command_str"
docker exec -it "$CONTAINER_NAME" bash -c "python $CLI_PATH $command_str"