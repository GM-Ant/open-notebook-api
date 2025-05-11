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

    def test_concurrent_singleton(self):
        """Test singleton behavior under concurrent access"""
        from concurrent.futures import ThreadPoolExecutor
        registries = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(ToolRegistry) for _ in range(5)]
            registries = [f.result() for f in futures]

        assert all(r is registries[0] for r in registries)

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
            data = response.json()
            assert "test_tool" in data
            # Validate OpenAPI schema structure
            assert "type" in data["test_tool"]
            assert "description" in data["test_tool"]
            assert "parameters" in data["test_tool"]

    @pytest.mark.parametrize("tool_name,expected_status", [
        ("invalid tool!", 422),  # Invalid characters
        ("nonexistent_tool", 404),  # Valid format but missing
        ("../../malicious", 422),  # Path traversal attempt
        ("", 422)  # Empty tool name
    ])
    def test_get_tool_error_cases(self, test_client, tool_registry, tool_name, expected_status):
        """Test error handling for invalid tool requests"""
        with patch('open_notebook_mcp.main.tool_registry', tool_registry):
            response = test_client.get(f"/tools/{tool_name}")
            assert response.status_code == expected_status

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

    def test_healthcheck_endpoint(self, test_client, tool_registry):
        """Test registry health verification endpoint"""
        with patch('open_notebook_mcp.main.tool_registry', tool_registry):
            # Test healthy state
            response = test_client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

            # Test degraded state
            tool_registry._tools = {}
            response = test_client.get("/health")
            assert response.status_code == 503

class TestCLIErrorHandling:
    def test_cli_reflection_failure(self, test_client, caplog):
        """Test handling of CLI reflection errors"""
        with patch('open_notebook.tool_registry.CLIInspector.generate_all_schemas') as mock_reflect:
            mock_reflect.side_effect = RuntimeError("Reflection failed")
            
            # Test failure propagates to healthcheck
            response = test_client.get("/health")
            assert response.status_code == 503
            
            # Verify error logging
            assert "Reflection failed" in caplog.text

    def test_partial_cli_failure(self, test_client):
        """Test handling of partial CLI reflection failures"""
        with patch('open_notebook.tool_registry.CLIInspector.generate_all_schemas') as mock_reflect:
            # Mock one valid and one invalid tool
            mock_reflect.return_value = {
                "valid_tool": ToolSpec(
                    name="valid_tool",
                    description="Working tool",
                    parameters=ToolParameters(
                        type="object",
                        properties={}
                    )
                ),
                "invalid_tool": None  # Simulate reflection failure
            }
            
            response = test_client.get("/health")
            assert response.status_code == 206  # Partial content

@pytest.fixture
def mock_cli_commands():
    """Fixture providing mocked CLI command outputs"""
    return {
        "valid_command": argparse.Namespace(
            description="Valid command",
            params=[argparse.ArgumentParser(add_help=False)]
        ),
        "error_command": argparse.Namespace(
            description="Broken command",
            params=[argparse.ArgumentParser(add_help=False)]
        )
    }

@pytest.fixture
def error_injection():
    """Fixture for injecting various error types"""
    errors = {
        'value_error': ValueError("Invalid value"),
        'type_error': TypeError("Invalid type"),
        'runtime_error': RuntimeError("Runtime failure")
    }
    return errors
