#!/usr/bin/env python
"""
Generate example JSON schema outputs for CLI commands.

This script uses the CLIInspector to generate OpenAI function-calling schemas
for the specified CLI commands and saves them to JSON files.
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path if needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from open_notebook.tool_reflector import CLIInspector


def main():
    """Generate and save example schemas."""
    # Create the examples/schemas directory if it doesn't exist
    output_dir = Path(__file__).parent / "schemas"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize the CLIInspector
    inspector = CLIInspector()
    
    # Commands to generate schemas for
    commands = ["list-notebooks", "add-url-source", "text-search"]
    
    for command in commands:
        # Generate the schema
        schema = inspector.generate_schema_for_command(command)
        if not schema:
            print(f"Error: Could not generate schema for command '{command}'")
            continue
        
        # Convert to dict for JSON serialization
        schema_dict = schema.model_dump()
        
        # Save to file
        output_file = output_dir / f"{command}_schema.json"
        with open(output_file, "w") as f:
            json.dump(schema_dict, f, indent=2)
        
        print(f"Generated schema for '{command}' saved to {output_file}")


if __name__ == "__main__":
    main()