#!/usr/bin/env python
"""
Tool Registry - Registry for OpenAI function-calling schemas generated from CLI commands

This module provides a singleton registry for storing and retrieving OpenAI function-calling schemas
that are generated from the Open Notebook CLI commands. The registry maintains an in-memory cache
of tool schemas and provides lookup capabilities by tool name.
"""

import logging
import threading
from typing import Dict, Optional, List, Any # Added List, Any

from pydantic import BaseModel

from open_notebook.tool_reflector import CLIInspector # Keep this import
# Forward declaration for ToolSpecInternal if CLIInspector needs it, or define ArgumentSpec here

logger = logging.getLogger(__name__)

# Internal representation of an argument, closer to argparse
class ArgumentSpec(BaseModel):
    name: str
    type: str  # JSON schema type: string, integer, number, boolean, array
    description: Optional[str] = None
    required: bool
    default: Optional[Any] = None
    choices: Optional[List[Any]] = None
    is_flag: bool = False # True if it's a store_true/store_false type flag
    items_type: Optional[str] = None # For array type, the type of its items

# Internal representation of a tool/command
class ToolSpecInternal(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: List[ArgumentSpec]

# Public-facing OpenAI-compatible schema for a parameter
class ParameterSchema(BaseModel):
    type: str
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None
    items: Optional[Dict[str, str]] = None # For array type in JSON schema

# Public-facing OpenAI-compatible schema for a tool
class ToolSchema(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, ParameterSchema]

class ToolRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized_flag') and self._initialized_flag:
            return
        with self._lock:
            if hasattr(self, '_initialized_flag') and self._initialized_flag:
                return
            self._tools: Dict[str, ToolSpecInternal] = {} # Stores internal spec
            self._cli_inspector: Optional[CLIInspector] = None
            self._initialized_flag = True
            logger.debug("ToolRegistry initialized.")

    def is_initialized(self) -> bool:
        return hasattr(self, '_initialized_flag') and self._initialized_flag

    def _ensure_inspector(self, cli_script_path: Optional[str] = None) -> bool:
        if self._cli_inspector and (not cli_script_path or self._cli_inspector.cli_script_path == cli_script_path):
            return True
        if cli_script_path:
            logger.info(f"Configuring ToolRegistry's CLIInspector with script path: {cli_script_path}")
            # Assuming CLIInspector can be initialized with cli_script_path or has a method to set it.
            # For now, let's assume CLIInspector takes it in constructor or we adapt CLIInspector
            self._cli_inspector = CLIInspector(cli_script_path=cli_script_path)
            return True
        if not self._cli_inspector:
             logger.error("CLIInspector not available and no cli_script_path provided to configure it.")
             return False
        return True

    def load_tools(self, tools: Optional[Dict[str, ToolSpecInternal]] = None, cli_script_path: Optional[str] = None) -> None:
        if not self.is_initialized():
            logger.error("ToolRegistry.load_tools() called on uninitialized instance.")
            return

        logger.info("Loading tool specifications into ToolRegistry...")
        try:
            if tools is not None:
                self._tools = tools
                logger.info(f"Successfully loaded {len(self._tools)} pre-generated tool specs.")
            elif self._ensure_inspector(cli_script_path) and self._cli_inspector:
                # Assuming CLIInspector.generate_all_schemas() will return Dict[str, ToolSpecInternal]
                self._tools = self._cli_inspector.generate_all_internal_specs() # Method to be created in CLIInspector
                logger.info(f"Successfully generated and loaded {len(self._tools)} tool specs from {self._cli_inspector.cli_script_path}.")
            else:
                logger.error("Cannot load tools: No pre-generated tools provided and CLI inspector could not be configured.")
                self._tools = {}
                return
        except Exception as e:
            logger.error(f"Error loading tool specifications: {e}", exc_info=True)
            self._tools = {}

    def get_tool_spec(self, tool_name: str) -> Optional[ToolSpecInternal]:
        if not self.is_initialized():
            logger.warning("ToolRegistry.get_tool_spec() called before fully initialized.")
            return None
        spec = self._tools.get(tool_name)
        if not spec:
            logger.warning(f"ToolSpecInternal for '{tool_name}' not found in registry.")
        return spec

    def _convert_arg_spec_to_parameter_schema(self, arg_spec: ArgumentSpec) -> ParameterSchema:
        param_schema_args = {
            "type": arg_spec.type,
            "description": arg_spec.description,
        }
        if arg_spec.choices:
            param_schema_args["enum"] = arg_spec.choices
        if arg_spec.default is not None: # Consider how to handle SUPPRESS_DEFAULT from argparse if needed
            param_schema_args["default"] = arg_spec.default
        if arg_spec.type == "array" and arg_spec.items_type:
            param_schema_args["items"] = {"type": arg_spec.items_type}
        
        return ParameterSchema(**param_schema_args)

    def _convert_to_schema(self, tool_spec_internal: ToolSpecInternal) -> ToolSchema:
        parameters: Dict[str, ParameterSchema] = {}
        required_params: List[str] = [] # For OpenAI schema's top-level required list

        for arg_spec in tool_spec_internal.arguments:
            parameters[arg_spec.name] = self._convert_arg_spec_to_parameter_schema(arg_spec)
            if arg_spec.required:
                required_params.append(arg_spec.name)
        
        # Construct the parameters part of the OpenAI schema
        # The actual OpenAI schema has parameters.properties and parameters.required
        # So, the ToolSchema.parameters should represent the `properties` field.
        # The `required` list goes into the `ToolParameters` object in the OpenAI schema.
        # For simplicity here, ToolSchema.parameters IS the properties dict.
        # If a more direct mapping to OpenAI is needed, ToolSchema might need adjustment or
        # this function returns the full parameter object including type:object, properties, and required.

        # For now, ToolSchema.parameters is the properties dict.
        # The `required` list is implicitly handled by ParameterSchema.required, but OpenAI schema has it at the parent level.
        # Let's adjust ToolSchema to better match OpenAI's direct structure for a tool
        # For now, I will keep ToolSchema as is and assume the consumer knows how to use it.
        # The `required` field in `ParameterSchema` is a bit misleading if mapping directly to OpenAI.
        # Let's assume `ParameterSchema.required` is for informational purpose for now.

        return ToolSchema(
            name=tool_spec_internal.name,
            description=tool_spec_internal.description,
            parameters=parameters # This is the `properties` part of OpenAI schema
        )

    def get_tool(self, tool_name: str) -> Optional[ToolSchema]:
        tool_spec_internal = self.get_tool_spec(tool_name)
        if not tool_spec_internal:
            return None
        return self._convert_to_schema(tool_spec_internal)

    def get_all_tool_schemas(self) -> Dict[str, ToolSchema]:
        if not self.is_initialized():
            logger.warning("ToolRegistry.get_all_tool_schemas() called before fully initialized.")
            return {}
        
        schemas: Dict[str, ToolSchema] = {}
        for name, spec_internal in self._tools.items():
            schemas[name] = self._convert_to_schema(spec_internal)
        return schemas

    def get_all_tools_dict_internal(self) -> Dict[str, ToolSpecInternal]:
        """Retrieves all loaded internal tool specs as a dictionary."""
        if not self.is_initialized():
            logger.warning("ToolRegistry.get_all_tools_dict_internal() called before fully initialized.")
            return {}
        return self._tools

# Global instance of the registry
tool_registry = ToolRegistry()