# Phase 3 Implementation Plan: Tool Registry & API Endpoints

**Overall Goal:** Create a robust, in-memory tool registry that loads CLI command schemas at application startup and exposes them via FastAPI endpoints, complete with comprehensive tests and documentation.

## User Feedback and Clarifications Incorporated:
*   **Singleton Implementation:** A module-level instance for `ToolRegistry` is acceptable.
*   **Startup Error Behavior:** The FastAPI application should start even if schema loading fails, logging the errors. The `/tools` endpoints might return empty or partial data in such cases.
*   **Pydantic Models:** The use of `ToolSpec` and `List[ToolSpec]` for the API endpoint response models is correct.
*   **Test File Location:** New tests for the `ToolRegistry` and its API endpoints will be placed in a new file: `tests/test_tool_registry_api.py`.

## 1. Implement `ToolRegistry` Class

**File:** `open_notebook/tool_registry.py`

**Objective:** Create a singleton class to manage tool schemas.

*   **Class Definition:**
    *   Define a class `ToolRegistry`.
    *   Utilize a module-level instance for singleton behavior.
    ```python
    # In open_notebook/tool_registry.py
    import logging
    from typing import Dict, List, Optional
    
    from open_notebook.tool_reflector import CLIInspector, ToolSpec # Ensure this import is uncommented and correct
    
    logger = logging.getLogger(__name__)
    
    class ToolRegistry:
        _instance = None
    
        def __new__(cls, *args, **kwargs):
            if not cls._instance:
                cls._instance = super(ToolRegistry, cls).__new__(cls, *args, **kwargs)
            return cls._instance
    
        def __init__(self):
            if not hasattr(self, '_initialized'): # Ensure __init__ runs only once
                self._tools: Dict[str, ToolSpec] = {}
                self._cli_inspector = CLIInspector()
                self._initialized = True
                # Loading will be triggered by the FastAPI startup event.
    
        def load_tools(self) -> None:
            """
            Loads all CLI command schemas using CLIInspector and populates the registry.
            Handles errors during schema generation.
            """
            logger.info("Loading tool schemas...")
            try:
                schemas = self._cli_inspector.generate_all_schemas()
                self._tools = schemas # schemas is Dict[str, ToolSpec]
                logger.info(f"Successfully loaded {len(self._tools)} tool schemas.")
            except Exception as e:
                logger.error(f"Error loading tool schemas: {e}", exc_info=True)
                self._tools = {} # Ensure registry is empty on error
    
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
    ```
*   **Error Handling:** The `load_tools` method includes `try-except` blocks to catch and log errors from `CLIInspector`, and clears `_tools` on failure.

## 2. Update FastAPI Application

**File:** `api_main.py`

**Objective:** Integrate `ToolRegistry` and add new `/tools` endpoints.

*   **Imports:**
    *   Add `from open_notebook.tool_registry import tool_registry`
    *   Ensure `from open_notebook.tool_reflector import ToolSpec` is present for response models.
    *   Add `from typing import List` if not already present.
*   **Startup Event Handler:**
    ```python
    # In api_main.py
    # ... other imports ...
    from open_notebook.tool_registry import tool_registry
    from open_notebook.tool_reflector import ToolSpec # For response models
    from typing import List # Ensure List is imported
    
    # ... FastAPI app initialization ...
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("Application startup: Initializing Tool Registry...")
        try:
            tool_registry.load_tools() # Load schemas into the singleton instance
            if tool_registry.get_all_tools():
                 logger.info("Tool Registry initialized successfully and tools are loaded.")
            else:
                 logger.warning("Tool Registry initialized, but no tools were loaded. Check previous errors.")
        except Exception as e:
            logger.error(f"Failed to initialize Tool Registry during startup: {e}", exc_info=True)
            # Application will continue, but /tools endpoints might be empty or raise errors
    ```
*   **`/tools` Endpoint (List All Tools):**
    ```python
    @app.get("/tools",
             response_model=List[ToolSpec],
             summary="List all available tool schemas",
             response_description="A list of OpenAI-compatible tool schemas.")
    async def list_tools():
        """
        Retrieves a complete list of available tool schemas.
        These schemas are compatible with OpenAI's function-calling feature.
        """
        tools = tool_registry.get_all_tools()
        # No explicit check for empty tools here, as startup log covers it.
        # FastAPI will correctly return an empty list if no tools are loaded.
        return tools
    ```
*   **`/tools/{tool_name}` Endpoint (Get Specific Tool):**
    ```python
    @app.get("/tools/{tool_name}",
             response_model=ToolSpec,
             summary="Get a specific tool schema by name",
             response_description="The OpenAI-compatible schema for the specified tool.")
    async def get_tool_by_name(tool_name: str):
        """
        Retrieves the OpenAI-compatible schema for a single tool, identified by its name.
        Returns a 404 error if the tool is not found.
        """
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            logger.warning(f"Tool '{tool_name}' not found in registry.")
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
        return tool
    ```

## 3. Implement Tests

**File:** `tests/test_tool_registry_api.py` (New File)

**Objective:** Ensure 100% test coverage for `ToolRegistry` and verify API endpoints.

*   **`ToolRegistry` Tests:**
    *   **Singleton Test:** Verify that multiple calls to `ToolRegistry()` return the same instance.
    *   **Initialization & Loading:**
        *   Mock `CLIInspector.generate_all_schemas()` to return a predefined set of `ToolSpec` objects.
        *   Test `tool_registry.load_tools()`:
            *   Verify `_cli_inspector.generate_all_schemas` is called.
            *   Verify `tool_registry._tools` is populated correctly.
        *   Test error handling: Mock `generate_all_schemas` to raise an exception and verify logging and that `_tools` is empty.
    *   **`get_tool()` Tests:**
        *   Test retrieving an existing tool.
        *   Test retrieving a non-existent tool (should return `None`).
    *   **`get_all_tools()` and `get_all_tools_dict()` Tests:**
        *   Verify they return the expected list/dictionary of `ToolSpec` objects.
*   **API Endpoint Tests (using `TestClient` from FastAPI):**
    *   **Setup:**
        *   Use a fixture to provide a `TestClient`.
        *   Mock `tool_registry.load_tools()` or `CLIInspector.generate_all_schemas()` within tests to provide controlled tool data for API test scenarios.
    *   **`GET /tools` Tests:**
        *   Verify 200 OK status.
        *   Verify response is a list.
        *   Verify each item in the list matches the `ToolSpec` schema.
        *   Test with an empty registry (e.g., mock `tool_registry.get_all_tools()` to return an empty list).
    *   **`GET /tools/{tool_name}` Tests:**
        *   Verify 200 OK for an existing tool and correct `ToolSpec` data.
        *   Verify 404 Not Found for a non-existent tool.

## 4. Documentation and Examples

*   **OpenAPI Documentation:**
    *   After implementation, run the FastAPI application.
    *   Access the auto-generated OpenAPI documentation (usually at `/docs` or `/redoc`).
    *   Verify that the new `/tools` and `/tools/{tool_name}` endpoints are present with correct request/response schemas.
    *   Take a screenshot for the completion deliverables.
*   **Example Curl Commands:**
    *   Create `examples/api-calls/tool_endpoints.sh` (or `.md`).
    *   Add commands:
        ```bash
        #!/bin/bash
        # Script to demonstrate API calls to /tools endpoints
        
        API_BASE_URL="http://localhost:8000" # Adjust if your API runs on a different port
        
        echo "Fetching all tool schemas..."
        curl -X GET "${API_BASE_URL}/tools" -H "accept: application/json"
        echo -e "\n\n"
        
        # Replace 'list-notebooks' with an actual tool name from your CLI if different
        TOOL_NAME_EXAMPLE="list-notebooks" 
        echo "Fetching schema for tool: ${TOOL_NAME_EXAMPLE}..."
        curl -X GET "${API_BASE_URL}/tools/${TOOL_NAME_EXAMPLE}" -H "accept: application/json"
        echo -e "\n"
        ```

## Mermaid Diagram: Component Interaction

```mermaid
graph TD
    A[FastAPI App Startup] -- triggers --> B(startup_event);
    B -- calls tool_registry.load_tools() --> C(ToolRegistry Singleton);
    C -- uses --> D(CLIInspector);
    D -- generates schemas from --> E(OpenNotebookCLI argparse);
    C -- stores --> F{In-Memory Schemas (Dict[str, ToolSpec])};

    G[HTTP GET /tools] -- routed by FastAPI --> H(list_tools Endpoint);
    H -- calls get_all_tools() --> C;
    C -- retrieves from --> F;
    H -- returns List[ToolSpec] --> I(User/Client);

    J[HTTP GET /tools/{tool_name}] -- routed by FastAPI --> K(get_tool_by_name Endpoint);
    K -- calls get_tool(tool_name) --> C;
    C -- retrieves from --> F;
    K -- returns ToolSpec or 404 --> I;

    L[Pytest TestClient] -- calls --> G;
    L -- calls --> J;
    M[Pytest Unit Tests] -- directly tests methods of --> C;