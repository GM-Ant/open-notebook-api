#!/usr/bin/env python
"""
Tool Registry - Registry for OpenAI function-calling schemas generated from CLI commands

This module provides a singleton registry for storing and retrieving OpenAI function-calling schemas
that are generated from the Open Notebook CLI commands. The registry maintains an in-memory cache
of tool schemas and provides lookup capabilities by tool name.
"""

import logging
from typing import Dict, List, Optional

from open_notebook.tool_reflector import CLIInspector, ToolSpec
from typing import Dict, List, Optional

from open_notebook.tool_reflector import CLIInspector, ToolSpec

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Singleton registry for managing tool schemas generated from CLI commands.
    Maintains an in-memory cache of OpenAI-compatible tool schemas.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ToolRegistry, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Ensure __init__ runs only once
            self._tools: Dict[str, ToolSpec] = {}
            self._cli_inspector = CLIInspector()
            self._initialized = True

    def load_tools(self) -> None:
        """
        Loads all CLI command schemas using CLIInspector and populates the registry.
        Handles errors during schema generation.
        """
        logger.info("Loading tool schemas...")
        try:
            schemas = self._cli_inspector.generate_all_schemas()
            self._tools = schemas
            logger.info(f"Successfully loaded {len(self._tools)} tool schemas.")
        except Exception as e:
            logger.error(f"Error loading tool schemas: {e}", exc_info=True)
            self._tools = {}  # Clear registry on error

    def get_tool(self, tool_name: str) -> Optional[ToolSpec]:
        """Retrieves a tool schema by its name."""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[ToolSpec]:
        """Retrieves all tool schemas as a list."""
        return list(self._tools.values())

    def get_all_tools_dict(self) -> Dict[str, ToolSpec]:
        """Retrieves all tool schemas as a dictionary."""
        return self._tools


# Module-level instance for singleton behavior
tool_registry = ToolRegistry()