#!/usr/bin/env python3
"""
open_notebook_wrapper.py

A Python wrapper script for interacting with Open Notebook CLI from outside the Docker container.
This script forwards commands to the Open Notebook CLI running inside the container.

Usage:
    python open_notebook_wrapper.py <command> [options]

Example:
    python open_notebook_wrapper.py list-notebooks
    python open_notebook_wrapper.py create-notebook "My Research" "Notes about my research"
    python open_notebook_wrapper.py add-text-source notebook:abc123 "Title" "Content"

Run python open_notebook_wrapper.py --help for a list of available commands.
"""

import argparse
import json
import subprocess
import sys


class OpenNotebookWrapper:
    """Wrapper for Open Notebook CLI to run commands from outside the Docker container"""

    def __init__(self):
        # Configuration
        self.container_name = "assistant-notebook-1"
        self.cli_path = "open_notebook_cli.py"

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
            description='Open Notebook CLI Wrapper',
            add_help=False  # We'll handle help ourselves
        )
        parser.add_argument('--help', '-h', action='store_true', help='Show help message')
        return parser

    def run_command(self, args):
        """Run a command inside the container"""
        # Special case for help
        if len(args) == 0 or args[0] in ['--help', '-h']:
            self.show_help()
            return
            
        # Special case for shell access
        if args[0] == 'shell':
            print(f"Entering shell in container {self.container_name}...")
            subprocess.run(["docker", "exec", "-it", self.container_name, "bash"])
            return
            
        # Construct the command to run inside the container
        docker_cmd = ["docker", "exec", "-it", self.container_name, "python", self.cli_path]
        docker_cmd.extend(args)
        
        # Print what we're executing
        cmd_display = " ".join(["python", self.cli_path] + args)
        print(f"Executing: {cmd_display}")
        
        # Run the command
        try:
            subprocess.run(docker_cmd)
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nCommand interrupted")
            sys.exit(130)

    def show_usage(self):
        """Display basic usage information"""
        print("Open Notebook CLI Wrapper")
        print("")
        print("Usage:")
        print("  python open_notebook_wrapper.py <command> [options]")
        print("")
        print("Examples:")
        print("  python open_notebook_wrapper.py list-notebooks")
        print("  python open_notebook_wrapper.py create-notebook \"My Research\" \"Description\"")
        print("  python open_notebook_wrapper.py add-url-source notebook:abc123 https://example.com")
        print("")
        print("For more information, use:")
        print("  python open_notebook_wrapper.py --help")

    def show_help(self):
        """Show full help by forwarding to the CLI's help"""
        subprocess.run([
            "docker", "exec", "-it", 
            self.container_name, "python", self.cli_path, "--help"
        ])

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