import logging
import os
from fastapi import FastAPI, HTTPException, Request
from open_notebook.tool_registry import tool_registry
from open_notebook.tool_reflector import CLIInspector
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
async def load_tool_schemas():
    """Initialize tool registry by loading CLI commands"""
    try:
        logger.info("Initializing MCP server and loading tools...")
        inspector = CLIInspector()
        # Get the absolute path to the CLI file
        cli_path = "/app/open_notebook_cli.py"
        if not os.path.exists(cli_path):
            cli_path = "open_notebook_cli.py"
            logger.warning(f"Using relative path for CLI: {cli_path}")
        else:
            logger.info(f"Using absolute path for CLI: {cli_path}")
            
        commands = inspector.load_commands_from_file(cli_path)
        tool_registry.load_tools(commands)
        logger.info(f"Successfully loaded {len(commands)} tools")
    except Exception as e:
        logger.error(f"Failed to load tool schemas: {str(e)}")
        raise

@app.get("/")
async def read_root():
    return {"message": "Open Notebook MCP Server is running"}

@app.get("/health")
async def health_check():
    """Enhanced healthcheck that verifies registry initialization"""
    if not tool_registry.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Tool registry not initialized"
        )
    return {
        "status": "ok",
        "tools_loaded": len(tool_registry.get_all_tools_dict())
    }

@app.get("/tools")
async def list_tools():
    """Returns all available tools in OpenAI-compatible schema format"""
    return tool_registry.get_all_tools_dict()

@app.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Returns a specific tool schema by name"""
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool

@app.post("/execute/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Executes a tool by name with the provided parameters"""
    try:
        params = await request.json()
        logger.info(f"Executing tool {tool_name} with params: {params}")
        
        # Get the tool definition
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        # Execute the CLI command using the tool registry
        result = tool_registry.execute_tool(tool_name, params)
        
        return {"status": "success", "result": result}
    except Exception as e:
        logger.exception(f"Error executing tool {tool_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error executing tool: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)