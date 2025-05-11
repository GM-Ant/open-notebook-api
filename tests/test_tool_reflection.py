#!/usr/bin/env python
"""
Tests for the tool_reflector module.

This module contains tests for the tool_reflector module, which converts argparse CLI
configurations to OpenAI function-calling schemas.
"""

import argparse
import pytest
from unittest.mock import MagicMock, patch

from open_notebook.tool_reflector import (
    CLIInspector, 
    ToolParameterProperties, 
    ToolParameters, 
    ToolSpec
)
from open_notebook.tool_registry import ToolRegistry
from fastapi.testclient import TestClient
from open_notebook_mcp.main import app


@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def tool_registry():
    registry = ToolRegistry()
    registry._tools = {  # Bypass loading for testing
        "test_tool": ToolSpec(
            name="test_tool",
            description="Test tool",
            parameters=ToolParameters(
                type="object",
                properties={
                    "param1": ToolParameterProperties(
                        type="string",
                        description="Test parameter"
                    )
                },
                required=["param1"]
            )
        )
    }
    return registry

class TestToolRegistry:
    def test_singleton_pattern(self):
        """Test that ToolRegistry maintains singleton behavior"""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        assert registry1 is registry2

    def test_load_tools(self, tool_registry):
        """Test that tools can be loaded"""
        with patch.object(tool_registry._cli_inspector, 'generate_all_schemas') as mock_gen:
            mock_gen.return_value = {"mock_tool": "mock_schema"}
            tool_registry.load_tools()
            assert "mock_tool" in tool_registry._tools

    def test_get_tool(self, tool_registry):
        """Test retrieving a tool by name"""
        tool = tool_registry.get_tool("test_tool")
        assert tool.name == "test_tool"
        assert tool_registry.get_tool("nonexistent") is None

    def test_get_all_tools(self, tool_registry):
        """Test retrieving all tools"""
        tools = tool_registry.get_all_tools()
        assert len(tools) == 1
        assert tools[0].name == "test_tool"

    def test_get_all_tools_dict(self, tool_registry):
        """Test retrieving all tools as dict"""
        tools = tool_registry.get_all_tools_dict()
        assert len(tools) == 1
        assert "test_tool" in tools

class TestToolEndpoints:
    def test_list_tools_endpoint(self, test_client, tool_registry):
        """Test the /tools endpoint"""
        with patch('open_notebook_mcp.main.tool_registry', tool_registry):
            response = test_client.get("/tools")
            assert response.status_code == 200
            assert "test_tool" in response.json()

    def test_get_tool_endpoint(self, test_client, tool_registry):
        """Test the /tools/{tool_name} endpoint"""
        with patch('open_notebook_mcp.main.tool_registry', tool_registry):
            # Test existing tool
            response = test_client.get("/tools/test_tool")
            assert response.status_code == 200
            assert response.json()["name"] == "test_tool"

            # Test non-existent tool
            response = test_client.get("/tools/nonexistent")
            assert response.status_code == 404