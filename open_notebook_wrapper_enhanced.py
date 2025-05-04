#!/usr/bin/env python3
"""
open_notebook_wrapper_enhanced.py

An enhanced Python wrapper script for interacting with Open Notebook CLI from outside the Docker container.
This version automatically installs missing dependencies when needed.

Usage:
    python open_notebook_wrapper_enhanced.py <command> [options]

Example:
    python open_notebook_wrapper_enhanced.py list-notebooks
    python open_notebook_wrapper_enhanced.py create-notebook "My Research" "Notes about my research"
"""

import argparse
import json
import re
import subprocess
import sys


class OpenNotebookWrapper:
    """Enhanced wrapper for Open Notebook CLI to run commands from outside the Docker container"""

    def __init__(self):
        # Configuration
        self.container_name = "assistant-notebook-1"
        self.cli_path = "open_notebook_cli.py"
        # Common dependencies that might be missing
        self.common_dependencies = [
            "loguru",
            "pydantic",
            "langchain",
            "langgraph",
            "streamlit",
            "podcastfy"
        ]

    def check_container(self):
        """Check if the container is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            container_names = result.stdout.strip().split('\n')
            
            if self.container_name not in container_names:
                print(f"Error: Container '{self.container_name}' is not running")
                print("Please make sure the Open Notebook Docker container is started")
                sys.exit(1)
                
        except subprocess.CalledProcessError as e:
            print(f"Error checking Docker containers: {e}")
            print("Please make sure Docker is running")
            sys.exit(1)

    def create_parser(self):
        """Create a simple argument parser to handle help and shell commands"""
        parser = argparse.ArgumentParser(
            description='Enhanced Open Notebook CLI Wrapper',
            add_help=False  # We'll handle help ourselves
        )
        parser.add_argument('--help', '-h', action='store_true', help='Show help message')
        return parser

    def install_dependency(self, dependency):
        """Install a missing dependency in the container"""
        print(f"Installing missing dependency: {dependency}")
        try:
            # Try using uv first (preferred for Open Notebook)
            result = subprocess.run(
                ["docker", "exec", self.container_name, "uv", "pip", "install", dependency],
                capture_output=True,
                text=True
            )
            
            # If uv fails, try pip
            if result.returncode != 0:
                print("Falling back to pip...")
                subprocess.run(
                    ["docker", "exec", self.container_name, "pip", "install", dependency],
                    check=True
                )
                
            print(f"Successfully installed {dependency}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing {dependency}: {e}")
            return False

    def install_all_dependencies(self):
        """Install all common dependencies in the container"""
        print("Installing all common dependencies...")
        for dependency in self.common_dependencies:
            self.install_dependency(dependency)
        return True

    def run_command(self, args, retry_on_missing=True):
        """Run a command inside the container with automatic dependency handling"""
        # Special case for help
        if len(args) == 0 or args[0] in ['--help', '-h']:
            self.show_help()
            return
            
        # Special case for shell access
        if args[0] == 'shell':
            print(f"Entering shell in container {self.container_name}...")
            subprocess.run(["docker", "exec", "-it", self.container_name, "bash"])
            return
            
        # Special case for installing all dependencies
        if args[0] == 'install-dependencies':
            self.install_all_dependencies()
            return
            
        # Construct the command to run inside the container
        docker_cmd = ["docker", "exec", "-it", self.container_name, "python", self.cli_path]
        docker_cmd.extend(args)
        
        # Print what we're executing
        cmd_display = " ".join(["python", self.cli_path] + args)
        print(f"Executing: {cmd_display}")
        
        # Run the command and capture output to detect missing modules
        try:
            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            
            # Print the output
            if result.stdout:
                print(result.stdout)
                
            # Check for module not found error
            if result.returncode != 0 and result.stderr:
                print(result.stderr)
                
                # Check if this is a missing module error
                if "ModuleNotFoundError: No module named" in result.stderr and retry_on_missing:
                    # Extract the missing module name
                    match = re.search(r"No module named '([^']+)'", result.stderr)
                    if match:
                        missing_module = match.group(1)
                        # Install the missing module
                        if self.install_dependency(missing_module):
                            # Retry the command (only once to avoid infinite loops)
                            print("Retrying command...")
                            self.run_command(args, retry_on_missing=False)
                            return
                        
            return result.returncode
        except KeyboardInterrupt:
            print("\nCommand interrupted")
            sys.exit(130)

    def show_usage(self):
        """Display basic usage information"""
        print("Enhanced Open Notebook CLI Wrapper")
        print("")
        print("Usage:")
        print("  python open_notebook_wrapper_enhanced.py <command> [options]")
        print("")
        print("Examples:")
        print("  python open_notebook_wrapper_enhanced.py list-notebooks")
        print("  python open_notebook_wrapper_enhanced.py create-notebook \"My Research\" \"Description\"")
        print("")
        print("Special commands:")
        print("  shell                 - Enter a shell in the container")
        print("  install-dependencies  - Install all common dependencies")
        print("")
        print("For more information, use:")
        print("  python open_notebook_wrapper_enhanced.py --help")

    def show_help(self):
        """Show full help by forwarding to the CLI's help"""
        try:
            result = subprocess.run([
                "docker", "exec", "-it", 
                self.container_name, "python", self.cli_path, "--help"
            ], capture_output=True, text=True)
            
            if result.stdout:
                print(result.stdout)
            if result.stderr and "ModuleNotFoundError" in result.stderr:
                print("\nCannot display help due to missing dependencies.")
                print("Run 'python open_notebook_wrapper_enhanced.py install-dependencies' first.")
            elif result.stderr:
                print(result.stderr)
        except Exception as e:
            print(f"Error displaying help: {e}")

    def run(self):
        """Main method to run the wrapper"""
        # Check if the container is running
        self.check_container()
        
        # Parse arguments just to handle help
        parser = self.create_parser()
        args, unknown = parser.parse_known_args()
        
        # If no arguments, show usage
        if len(sys.argv) == 1:
            self.show_usage()
            return
            
        # If help flag is set, show help
        if args.help:
            self.show_help()
            return
            
        # Run the command with all arguments
        self.run_command(sys.argv[1:])


if __name__ == "__main__":
    wrapper = OpenNotebookWrapper()
    wrapper.run()