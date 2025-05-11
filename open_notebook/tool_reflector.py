#!/usr/bin/env python
"""
Tool Reflector - Converts argparse CLI configurations to OpenAI function-calling schemas

This module provides functionality to inspect argparse-based CLI tools and generate
compatible JSON schemas that can be used with OpenAI's function-calling API.
"""

import argparse
import inspect
import logging
from typing import Any, Dict, List, Optional, Type, Union, cast

from pydantic import BaseModel, Field

from open_notebook_cli import OpenNotebookCLI

# Setup logging
logger = logging.getLogger(__name__)


class ToolParameterProperties(BaseModel):
    """
    Represents the schema properties for a single parameter in the OpenAI function-calling format.
    """
    type: str
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None
    items: Optional[Dict[str, str]] = None


class ToolParameters(BaseModel):
    """
    Represents the parameters object in the OpenAI function-calling schema.
    """
    type: str = Field(default="object")
    properties: Dict[str, ToolParameterProperties]
    required: Optional[List[str]] = Field(default_factory=list)


class ToolSpec(BaseModel):
    """
    Represents the overall OpenAI function-calling schema for a CLI command.
    """
    name: str
    description: Optional[str] = None
    parameters: ToolParameters


class CLIInspector:
    """
    Inspects an argparse-based CLI and generates OpenAI function-calling schemas.
    """
    
    def __init__(self):
        """Initialize with an OpenNotebookCLI instance to inspect its parser."""
        self.cli = OpenNotebookCLI()
        self.parser = self.cli.parser
    
    def _get_subparser_action(self) -> argparse._SubParsersAction:
        """
        Find and return the _SubParsersAction instance from the main parser.
        This action holds the choices for all subcommands.
        
        Returns:
            The _SubParsersAction instance containing subcommand parsers
        
        Raises:
            ValueError: If no _SubParsersAction is found in the parser
        """
        for action in self.parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                return cast(argparse._SubParsersAction, action)
        
        raise ValueError("No subparsers found in the CLI parser")
    
    def _infer_arg_type(self, action: argparse.Action) -> str:
        """
        Infer the JSON Schema type from an argparse Action.
        
        Args:
            action: The argparse.Action to analyze
            
        Returns:
            A string representing the JSON Schema type ("string", "integer", "number", "boolean", or "array")
        """
        # Handle boolean flags
        if action.nargs == 0 and isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
            return "boolean"
        
        # Handle arrays (arguments that accept multiple values)
        if action.nargs in ('*', '+') or (isinstance(action.nargs, int) and action.nargs > 1):
            return "array"
        
        # Handle numeric types
        if action.type == int:
            return "integer"
        elif action.type == float:
            return "number"
        
        # Default to string for everything else
        return "string"
    
    def _extract_parameter_definition(self, arg_action: argparse.Action) -> ToolParameterProperties:
        """
        Extract parameter definition from an argparse Action.
        
        Args:
            arg_action: The argparse.Action to analyze
            
        Returns:
            A ToolParameterProperties instance with the extracted information
        """
        arg_type = self._infer_arg_type(arg_action)
        
        # Build the parameter properties
        properties = {
            "type": arg_type,
            "description": arg_action.help if arg_action.help else None,
        }
        
        # Add enum values if choices are specified
        if arg_action.choices is not None:
            properties["enum"] = list(arg_action.choices)
        
        # Add default value if specified and not suppressed
        if arg_action.default is not None and arg_action.default is not argparse.SUPPRESS:
            properties["default"] = arg_action.default
        
        # For array types, specify the items schema
        if arg_type == "array":
            item_type = "string"  # Default item type
            if arg_action.type == int:
                item_type = "integer"
            elif arg_action.type == float:
                item_type = "number"
            
            properties["items"] = {"type": item_type}
        
        return ToolParameterProperties(**properties)
    
    def generate_schema_for_command(self, command_name: str) -> Optional[ToolSpec]:
        """
        Generate an OpenAI function-calling schema for a specific command.
        
        Args:
            command_name: The name of the command to generate a schema for
            
        Returns:
            A ToolSpec instance representing the command's schema, or None if the command is not found
        """
        # Get the subparser action that contains all command parsers
        subparsers_action = self._get_subparser_action()
        
        # Check if the command exists
        if command_name not in subparsers_action.choices:
            logger.warning(f"Command '{command_name}' not found in CLI")
            return None
        
        # Get the parser for this specific command
        command_parser = subparsers_action.choices[command_name]
        
        # Extract command description
        description = command_parser.description or f"Execute the {command_name} command"
        
        # Build properties and required fields
        properties = {}
        required = []
        
        # Process each argument in the command parser
        for action in command_parser._actions:
            # Skip help actions
            if action.dest == 'help':
                continue
            
            # Extract parameter definition
            param_props = self._extract_parameter_definition(action)
            properties[action.dest] = param_props
            
            # Determine if this parameter is required
            is_required = False
            
            # Positional arguments (no option strings starting with -) are typically required
            if not action.option_strings:  # Positional argument
                # Unless they have nargs='?' or '*' which makes them optional
                if action.nargs not in ('?', '*'):
                    is_required = True
            # Optional arguments with required=True are required
            elif getattr(action, 'required', False):
                is_required = True
            
            if is_required:
                required.append(action.dest)
        
        # Create the ToolSpec
        tool_spec = ToolSpec(
            name=command_name,
            description=description,
            parameters=ToolParameters(
                properties=properties,
                required=required
            )
        )
        
        return tool_spec
    
    def generate_all_schemas(self) -> Dict[str, ToolSpec]:
        """
        Generate OpenAI function-calling schemas for all available commands.
        
        Returns:
            A dictionary mapping command names to their ToolSpec objects
        """
        subparsers_action = self._get_subparser_action()
        command_names = list(subparsers_action.choices.keys())
        
        schemas = {}
        for cmd_name in command_names:
            schema = self.generate_schema_for_command(cmd_name)
            if schema:
                schemas[cmd_name] = schema
        
        return schemas