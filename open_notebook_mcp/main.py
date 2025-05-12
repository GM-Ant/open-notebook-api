import logging
import os
from fastapi import FastAPI, HTTPException, Request
from typing import Dict # Added for response_model type hint

# Ensure tool_registry is imported correctly
from open_notebook.tool_registry import tool_registry, ToolSchema # Added ToolSchema for type hinting
# CLIInspector is used by the tool_registry internally, no need to import here directly for loading.
# from open_notebook.tool_reflector import CLIInspector 
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")

app = FastAPI(
    title="Open Notebook MCP Server",
    version="0.1.0",
    description="Provides MCP capabilities for Open Notebook.",
)

@app.on_event("startup")
async def startup_event_load_tools():
    """
    Initialize tool registry by loading CLI commands.
    This function is called by FastAPI when the application starts.
    """
    try:
        logger.info("MCP Server starting up. Initializing ToolRegistry...")
        
        # Determine the absolute path to the CLI script within the container
        # This path should align with where Dockerfile.mcp copies open_notebook_cli.py
        cli_script_path = "/app/open_notebook_cli.py" 
        
        if not os.path.exists(cli_script_path):
            # Fallback for local development if /app doesn't exist, though in Docker it should.
            alt_cli_path = "open_notebook_cli.py"
            logger.warning(
                f"Primary CLI path '{cli_script_path}' not found. "
                f"Attempting fallback to '{alt_cli_path}' for local dev."
            )
            if os.path.exists(alt_cli_path):
                cli_script_path = alt_cli_path
            else:
                logger.error(
                    f"Critical: CLI script not found at '{cli_script_path}' or '{alt_cli_path}'. "
                    "ToolRegistry will not be populated."
                )
                # Depending on desired behavior, could raise an exception to halt server startup
                # For now, it will continue, but /health will show 0 tools.
                return

        logger.info(f"Attempting to load tools from CLI script: {cli_script_path}")
        # The tool_registry now handles its own CLIInspector.
        # We pass the script path to load_tools.
        tool_registry.load_tools(cli_script_path=cli_script_path)
        
        if tool_registry.is_initialized() and len(tool_registry.get_all_tool_schemas()) > 0:
            logger.info(
                f"ToolRegistry initialized successfully. "
                f"Loaded {len(tool_registry.get_all_tool_schemas())} tool schemas."
            )
        elif tool_registry.is_initialized():
            logger.warning(
                "ToolRegistry initialized, but no tool schemas were loaded. "
                "Check CLI script and ToolReflector logic."
            )
        else:
            # This case should ideally not be reached if load_tools is called and sets the flag.
            logger.error(
                "ToolRegistry failed to initialize properly after load_tools call."
            )

    except Exception as e:
        logger.error(f"Critical error during MCP server startup and tool loading: {str(e)}", exc_info=True)
        # Depending on policy, you might want to re-raise to stop the server
        # or allow it to start in a degraded state (health check would fail).
        # For now, log and continue; health check will reflect the issue.
        # To halt: raise ApplicationError("Failed to initialize tool registry") from e


@app.get("/")
async def read_root():
    return {"message": "Open Notebook MCP Server is running"}

@app.get("/health")
async def health_check():
    """Enhanced healthcheck that verifies registry initialization and tool loading."""
    initialized = tool_registry.is_initialized()
    num_tools = 0
    if initialized:
        try:
            num_tools = len(tool_registry.get_all_tool_schemas())
        except Exception as e:
            logger.error(f"Error getting tool schemas for health check: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Error accessing tool registry during health check."
            )

    if not initialized:
        logger.warning("Health check: Tool registry is not initialized.")
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail="Tool registry not initialized. Server may be starting or encountered an error."
        )
    
    if num_tools == 0 and initialized: # Check initialized here again to be specific
        logger.warning("Health check: Tool registry is initialized but no tools are loaded.")
        return {
            "status": "ok_no_tools",
            "message": "Tool registry is initialized, but no tools are currently loaded.",
            "tools_loaded": 0
        }

    return {
        "status": "ok",
        "message": "Tool registry initialized and tools loaded.",
        "tools_loaded": num_tools
    }

@app.get("/tools", response_model=Dict[str, ToolSchema])
async def list_tools_endpoint():
    """Returns all available tools in OpenAI-compatible schema format."""
    if not tool_registry.is_initialized():
        raise HTTPException(status_code=503, detail="Tool registry not initialized.")
    try:
        schemas = tool_registry.get_all_tool_schemas()
        if not schemas and tool_registry.is_initialized(): # Check if initialized but empty
             logger.info("/tools endpoint: Registry initialized, but no tools found to return.")
        return schemas
    except Exception as e:
        logger.error(f"Error retrieving all tool schemas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve tool schemas.")


@app.get("/tools/{tool_name}", response_model=ToolSchema)
async def get_tool_endpoint(tool_name: str):
    """Returns a specific tool schema by name."""
    if not tool_registry.is_initialized():
        raise HTTPException(status_code=503, detail="Tool registry not initialized.")
    try:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            logger.warning(f"Tool '{tool_name}' not found in registry for /tools/{tool_name} endpoint.")
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
        return tool
    except HTTPException:
        raise # Re-raise HTTPException (like 404)
    except Exception as e:
        logger.error(f"Error retrieving tool schema for '{tool_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tool schema for '{tool_name}'.")


@app.post("/execute/{tool_name}")
async def execute_tool_endpoint(tool_name: str, request: Request):
    """
    Executes a tool by name with the provided parameters.
    NOTE: Actual execution logic is a placeholder and needs full implementation.
    """
    if not tool_registry.is_initialized():
        raise HTTPException(status_code=503, detail="Tool registry not initialized. Cannot execute tool.")

    try:
        params = await request.json()
        logger.info(f"Received request to execute tool '{tool_name}' with params: {params}")
        
        # Get the internal tool specification to understand its arguments
        tool_spec_internal = tool_registry.get_tool_spec(tool_name)
        if not tool_spec_internal:
            logger.warning(f"Execute request for unknown tool: '{tool_name}'")
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found, cannot execute.")
        
        # --- Placeholder for actual execution ---
        # TODO: Implement the logic to:
        # 1. Validate `params` against `tool_spec_internal.arguments`.
        # 2. Construct the command-line call to `open_notebook_cli.py`.
        # 3. Execute the command using `subprocess.run` or similar.
        # 4. Format the result (stdout/stderr) into a response.

        logger.warning(
            f"Execution logic for tool '{tool_name}' is currently a placeholder. "
            "No actual command will be run."
        )
        
        result = {
            "tool_name": tool_name,
            "parameters_received": params,
            "message": "Execution placeholder: Tool execution not yet implemented.",
            "output": None, 
            "error": None,  
            "return_code": None 
        }
        # --- End Placeholder ---
        
        return {"status": "success_placeholder", "result": result}

    except HTTPException:
        raise 
    except Exception as e:
        logger.exception(f"Error during placeholder execution of tool '{tool_name}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Server error while attempting to execute tool '{tool_name}': {str(e)}"
        )

if __name__ == "__main__":
    logger.info("Starting MCP server directly via __main__ (for local dev/testing)")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv("MCP_SERVER_PORT", "8001")) # Ensure port is string for getenv default
    )