#!/usr/bin/env python3
"""
open_notebook_container_setup.py

A comprehensive setup script for the Open Notebook Docker container.
This script diagnoses and fixes dependency issues in the container.

Usage:
    python open_notebook_container_setup.py
"""

import os
import subprocess
import sys
import time

# Configuration
CONTAINER_NAME = "assistant-notebook-1"
REQUIRED_PACKAGES = [
    "loguru",
    "pydantic",
    "langchain",
    "langgraph",
    "streamlit",
    "podcastfy",
    "typing_extensions",
    "humanize",
    "pyyaml"
]

def run_command(cmd, capture_output=True, check=True, shell=False):
    """Run a command and return the result"""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, check=check)
        else:
            result = subprocess.run(cmd, capture_output=capture_output, text=True, check=check)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        raise

def check_container():
    """Check if the container is running"""
    print("Checking if the Open Notebook container is running...")
    try:
        result = run_command(["docker", "ps", "--format", "{{.Names}}"])
        container_names = result.stdout.strip().split('\n')
        
        if CONTAINER_NAME not in container_names:
            print(f"Error: Container '{CONTAINER_NAME}' is not running")
            print("Please make sure the Open Notebook Docker container is started")
            return False
        
        print(f"Container '{CONTAINER_NAME}' is running.")
        return True
                
    except subprocess.CalledProcessError as e:
        print(f"Error checking Docker containers: {e}")
        print("Please make sure Docker is running")
        return False

def diagnose_python_environment():
    """Diagnose the Python environment in the container"""
    print("\n====== Diagnosing Python Environment ======")
    
    # Check which Python is being used
    print("Checking Python version and location...")
    run_command(["docker", "exec", CONTAINER_NAME, "which", "python"], capture_output=False)
    run_command(["docker", "exec", CONTAINER_NAME, "python", "--version"], capture_output=False)
    
    # Check Python path
    print("\nChecking Python module search paths...")
    run_command([
        "docker", "exec", CONTAINER_NAME, 
        "python", "-c", 
        "\"import sys; print('\\n'.join(sys.path))\""
    ], capture_output=False)
    
    # Check if uv is installed
    print("\nChecking if uv is available...")
    try:
        run_command(["docker", "exec", CONTAINER_NAME, "which", "uv"], capture_output=False)
        has_uv = True
    except subprocess.CalledProcessError:
        print("uv command not found. Will use pip instead.")
        has_uv = False
    
    # Check pip
    print("\nChecking pip installation...")
    run_command(["docker", "exec", CONTAINER_NAME, "pip", "--version"], capture_output=False)
    
    return has_uv

def install_dependencies(has_uv):
    """Install all required dependencies"""
    print("\n====== Installing Dependencies ======")
    
    # Force reinstall all dependencies
    for package in REQUIRED_PACKAGES:
        print(f"\nInstalling {package}...")
        
        if has_uv:
            # First try with uv
            try:
                run_command([
                    "docker", "exec", CONTAINER_NAME, 
                    "uv", "pip", "install", "--force-reinstall", package
                ], capture_output=False)
                continue  # If successful, move to next package
            except subprocess.CalledProcessError:
                print(f"Failed to install {package} with uv. Trying pip...")
        
        # Try with pip
        try:
            run_command([
                "docker", "exec", CONTAINER_NAME, 
                "pip", "install", "--force-reinstall", package
            ], capture_output=False)
        except subprocess.CalledProcessError:
            print(f"Failed to install {package} with pip. Trying with pip3...")
            
            # Last resort: try pip3
            try:
                run_command([
                    "docker", "exec", CONTAINER_NAME, 
                    "pip3", "install", "--force-reinstall", package
                ], capture_output=False)
            except subprocess.CalledProcessError:
                print(f"CRITICAL: Failed to install {package} with all methods!")

def create_cli_script():
    """Create or update the CLI script in the container"""
    print("\n====== Creating CLI Script in Container ======")
    
    # Prepare the directory for the CLI script in the container
    run_command(["docker", "exec", CONTAINER_NAME, "mkdir", "-p", "/app"], capture_output=False)
    
    # Before copying, check if the local CLI script exists
    if not os.path.exists("open_notebook_cli.py"):
        print("Error: Cannot find open_notebook_cli.py in the current directory.")
        return False
    
    # Copy the CLI script into the container
    print("Copying CLI script to container...")
    run_command([
        "docker", "cp", 
        "open_notebook_cli.py", 
        f"{CONTAINER_NAME}:/app/open_notebook_cli.py"
    ], capture_output=False)
    
    # Make it executable
    run_command([
        "docker", "exec", CONTAINER_NAME, 
        "chmod", "+x", "/app/open_notebook_cli.py"
    ], capture_output=False)
    
    return True

def verify_installation():
    """Verify that dependencies are properly installed"""
    print("\n====== Verifying Installation ======")
    
    all_successful = True
    for package in REQUIRED_PACKAGES:
        print(f"Checking if {package} is properly installed...")
        try:
            # Attempt to import the package
            cmd = f"import {package}; print('{package} successfully imported!')"
            result = run_command([
                "docker", "exec", CONTAINER_NAME, 
                "python", "-c", cmd
            ])
            print(result.stdout.strip())
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed to import {package}!")
            all_successful = False
    
    return all_successful

def run_test_command():
    """Run a test command to ensure CLI works"""
    print("\n====== Running Test Command ======")
    
    try:
        print("Running 'list-notebooks' command...")
        run_command([
            "docker", "exec", CONTAINER_NAME, 
            "python", "/app/open_notebook_cli.py", "list-notebooks"
        ], capture_output=False)
        return True
    except subprocess.CalledProcessError:
        return False

def create_run_script():
    """Create a simple run script for executing CLI commands"""
    print("\n====== Creating Run Script ======")
    
    script_content = """#!/bin/bash
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
"""
    
    # Write the script to a file
    with open("on_run.sh", "w") as f:
        f.write(script_content)
    
    # Make it executable
    os.chmod("on_run.sh", 0o755)
    
    print("Created 'on_run.sh' script for easy CLI execution.")
    print("Usage: ./on_run.sh <command> [options]")
    print("Example: ./on_run.sh list-notebooks")

def main():
    print("===== Open Notebook Container Setup =====\n")
    
    # Make sure the container is running
    if not check_container():
        return 1
    
    # Diagnose the Python environment
    has_uv = diagnose_python_environment()
    
    # Install all dependencies
    install_dependencies(has_uv)
    
    # Copy the CLI script into the container
    if not create_cli_script():
        print("Failed to create CLI script in container.")
        return 1
    
    # Verify installations
    if not verify_installation():
        print("\nWARNING: Some dependencies could not be imported.")
        print("The CLI may not work correctly.")
    else:
        print("\nAll dependencies successfully installed!")
    
    # Run a test command
    if run_test_command():
        print("\nTest command successful! The CLI is working properly.")
    else:
        print("\nWARNING: Test command failed. The CLI might not be working correctly.")
    
    # Create run script
    create_run_script()
    
    print("\n===== Setup Complete =====")
    print("You can now use './on_run.sh <command>' to interact with Open Notebook.")
    return 0

if __name__ == "__main__":
    sys.exit(main())