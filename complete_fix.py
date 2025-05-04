#!/usr/bin/env python3
"""
complete_fix.py - Complete fix for Open Notebook dependencies
"""

import subprocess
import sys

CONTAINER_NAME = "assistant-notebook-1"
ALL_DEPENDENCIES = [
    # Core dependencies
    "loguru", "pydantic", "langchain", "langgraph",
    # Database dependencies
    "sblpy", "surrealdb", 
    # Additional dependencies
    "pyyaml", "typing_extensions", "humanize",
    # Plugin dependencies
    "streamlit", "podcastfy"
]

def run_in_container(cmd, capture_output=True):
    """Run a command in the Docker container"""
    full_cmd = ["docker", "exec", CONTAINER_NAME] + cmd
    try:
        result = subprocess.run(full_cmd, capture_output=capture_output, text=True, check=True)
        return result.stdout if capture_output else None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return None

def check_container():
    """Check if the container is running"""
    try:
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], 
                              capture_output=True, text=True, check=True)
        return CONTAINER_NAME in result.stdout
    except subprocess.CalledProcessError:
        return False

def install_all_dependencies():
    """Install all required dependencies"""
    print("\n===== Installing All Dependencies =====")
    
    # Upgrade pip first
    print("Upgrading pip...")
    run_in_container(["pip", "install", "--upgrade", "pip"], capture_output=False)
    
    # Install all dependencies
    for dep in ALL_DEPENDENCIES:
        print(f"Installing {dep}...")
        run_in_container(["pip", "install", "--force-reinstall", dep], capture_output=False)
    
    print("\nAll dependencies installed!")

def verify_installations():
    """Verify all dependencies are installed correctly"""
    print("\n===== Verifying Installations =====")
    
    all_good = True
    for dep in ALL_DEPENDENCIES:
        print(f"Checking {dep}...")
        try:
            run_in_container(["python", "-c", f"import {dep}"], capture_output=False)
            print(f"✓ {dep} installed correctly")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to import {dep}!")
            all_good = False
    
    return all_good

def create_wrapper_script():
    """Create the updated wrapper script"""
    print("\n===== Creating Wrapper Script =====")
    
    script_content = """#!/bin/bash
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
  
  # Additional dependencies (yaml, etc.)"
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
"""
    
    with open("on_run.sh", "w") as f:
        f.write(script_content)
    
    # Make executable
    subprocess.run(["chmod", "+x", "on_run.sh"])
    
    print("Created wrapper script: on_run.sh")
    print("Usage: ./on_run.sh <command> [options]")

def main():
    print("===== Complete Open Notebook Dependency Fix =====")
    
    # Check if container is running
    if not check_container():
        print(f"Error: Container '{CONTAINER_NAME}' is not running.")
        print("Please start the container and try again.")
        return 1
    
    # Install all dependencies
    install_all_dependencies()
    
    # Verify installations
    if not verify_installations():
        print("\nWARNING: Some dependencies could not be installed correctly.")
    else:
        print("\nAll dependencies installed successfully!")
    
    # Create wrapper script
    create_wrapper_script()
    
    print("\n===== Fix Complete =====")
    print("Try running: ./on_run.sh list-notebooks")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())