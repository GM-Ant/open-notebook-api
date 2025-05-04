#!/bin/bash
# on_run.sh - Simple script to run Open Notebook CLI commands in the container

CONTAINER_NAME="assistant-notebook-1"
CLI_PATH="/app/open_notebook_cli.py"

if [ $# -eq 0 ]; then
  echo "Usage: ./on_run.sh <command> [options]"
  echo "Example: ./on_run.sh list-notebooks"
  exit 1
fi

# Run the command in the container
docker exec -it "$CONTAINER_NAME" python "$CLI_PATH" "$@"
