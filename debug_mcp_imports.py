# filepath: /Users/gregory/localcode/open-notebook/debug_mcp_imports.py
import os
import sys
import traceback

print("--- Python Environment ---")
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
print(f"Current working directory: {os.getcwd()}")

print("\n--- Environment Variables ---")
relevant_vars = [
    'ENABLE_MCP_SERVER', 'PYTHONPATH', 'SURREAL_ADDRESS', 'SURREAL_USER',
    'SURREAL_PASSWORD', 'SURREAL_NAMESPACE', 'SURREAL_DATABASE', 'SURREAL_SCOPE',
    'OPENAI_API_KEY', 'LOG_LEVEL'
]
for var in relevant_vars:
    print(f"{var}: {os.environ.get(var)}")

print("\n--- Attempting to import open_notebook ---")
try:
    import open_notebook
    print("Successfully imported 'open_notebook'")
    print(f"open_notebook location: {open_notebook.__file__}")
except Exception as e:
    print(f"ERROR importing 'open_notebook': {e}")
    traceback.print_exc()

print("\n--- Attempting to import open_notebook.tool_registry ---")
try:
    from open_notebook import tool_registry
    print("Successfully imported 'open_notebook.tool_registry'")
    print(f"tool_registry location: {tool_registry.__file__}")
except Exception as e:
    print(f"ERROR importing 'open_notebook.tool_registry': {e}")
    traceback.print_exc()

print("\n--- Attempting to import open_notebook_mcp ---")
try:
    import open_notebook_mcp
    print("Successfully imported 'open_notebook_mcp'")
    print(f"open_notebook_mcp location: {open_notebook_mcp.__file__}")
except Exception as e:
    print(f"ERROR importing 'open_notebook_mcp': {e}")
    traceback.print_exc()

print("\n--- Attempting to import open_notebook_mcp.main ---")
try:
    from open_notebook_mcp import main as mcp_main
    print("Successfully imported 'open_notebook_mcp.main'")
    print(f"mcp_main location: {mcp_main.__file__}")
except Exception as e:
    print(f"ERROR importing 'open_notebook_mcp.main': {e}")
    traceback.print_exc()

print("\n--- Checking for FastAPI and Uvicorn ---")
try:
    import fastapi
    import uvicorn # type: ignore
    print("FastAPI and Uvicorn are available.")
    print(f"FastAPI version: {fastapi.__version__}")
    print(f"Uvicorn version: {uvicorn.__version__}")
except ImportError as e:
    print(f"ERROR: FastAPI or Uvicorn not found: {e}")
except Exception as e:
    print(f"UNEXPECTED ERROR checking FastAPI/Uvicorn: {e}")
    traceback.print_exc()

print("\n--- Debug script finished ---")
