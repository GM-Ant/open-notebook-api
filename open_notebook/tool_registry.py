#!/usr/bin/env python
"""
Tool Registry - Registry for OpenAI function-calling schemas generated from CLI commands

This module provides a singleton registry for storing and retrieving OpenAI function-calling schemas
that are generated from the Open Notebook CLI commands. The registry maintains an in-memory cache
of tool schemas and provides lookup capabilities by tool name.
"""

import logging
import threading
from typing import Dict, List, Optional
from pydantic import BaseModel

from open_notebook.tool_reflector import CLIInspector, ToolSpec

logger = logging.getLogger(__name__)


class ParameterSchema(BaseModel):
    type: str
    description: str
    required: bool

class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: Dict[str, ParameterSchema]


class ToolRegistry:
    """
    Singleton registry for managing tool schemas generated from CLI commands.
    Maintains an in-memory cache of OpenAI-compatible tool schemas.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance.__init__()
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Ensure __init__ runs only once
            self._tools: Dict[str, ToolSpec] = {}
            self._cli_inspector = CLIInspector()
            self._initialized = True

    def load_tools(self, tools=None) -> None:
        """
        Loads tool schemas into the registry.
        
        Args:
            tools: Optional dict of pre-generated tool schemas. If None, generates all schemas from CLI.
        """
        logger.info("Loading tool schemas...")
        try:
            if tools is not None:
                self._tools = tools
            else:
                schemas = self._cli_inspector.generate_all_schemas()
                self._tools = schemas
            logger.info(f"Successfully loaded {len(self._tools)} tool schemas.")
        except Exception as e:
            logger.error(f"Error loading tool schemas: {e}", exc_info=True)
            self._tools = {}  # Clear registry on error

    def get_tool(self, tool_name: str) -> ToolSchema:
        """Retrieves a tool schema by its name."""
        if not self._tools:
            raise ValueError("Tool registry not initialized - call load_tools() first")
        
        if tool_name not in self._tools:
            raise KeyError(f"Tool {tool_name} not found in registry")
            
        return self._convert_to_schema(self._tools[tool_name])

    def _convert_to_schema(self, tool_spec: ToolSpec) -> ToolSchema:
        """Convert internal ToolSpec to public-facing ToolSchema"""
        params = {}
        for arg in tool_spec.arguments:
            params[arg.name] = ParameterSchema(
                type=arg.type,
                description=arg.description,
                required=arg.required
            )
        return ToolSchema(
            name=tool_spec.name,
            description=tool_spec.description,
            parameters=params
        )

    def get_all_tools(self) -> List[ToolSpec]:
        """Retrieves all tool schemas as a list."""
        return list(self._tools.values())

    def get_all_tools_dict(self) -> Dict[str, ToolSpec]:
        """Retrieves all tool schemas as a dictionary."""
        return self._tools
        
    def execute_tool(self, tool_name: str, params: dict) -> str:
        """
        Execute a tool by name with the provided parameters.
        
        Args:
            tool_name: The name of the tool to execute
            params: The parameters to pass to the tool
            
        Returns:
            The output of the tool execution
            
        Raises:
            ValueError: If the tool registry is not initialized
            KeyError: If the tool name is not found
            RuntimeError: If the tool execution fails
        """
        import subprocess
        import json
        
        if not self._tools:
            raise ValueError("Tool registry not initialized - call load_tools() first")
        
        if tool_name not in self._tools:
            raise KeyError(f"Tool {tool_name} not found in registry")
        
        # Construct the command to execute the CLI
        cmd = ["python", "open_notebook_cli.py", tool_name]
        
        # Add parameters as CLI arguments
        for param_name, param_value in params.items():
            if param_value is not None:
                # Handle boolean flags specially
                if isinstance(param_value, bool):
                    if param_value:
                        cmd.append(f"--{param_name}")
                # Handle arrays specially
                elif isinstance(param_value, list):
                    cmd.append(f"--{param_name}")
                    for item in param_value:
                        cmd.append(str(item))
                # Handle regular parameters
                else:
                    cmd.append(f"--{param_name}")
                    cmd.append(str(param_value))
        
        logger.info(f"Executing tool: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Tool execution failed: {e}, stderr: {e.stderr}")
            raise RuntimeError(f"Tool execution failed: {e.stderr}")


# Module-level instance for singleton behavior
tool_registry = ToolRegistry()