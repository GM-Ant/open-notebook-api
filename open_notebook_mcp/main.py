import logging
from fastapi import FastAPI, HTTPException
from open_notebook.tool_registry import tool_registry
from open_notebook.tool_reflector import CLIInspector

app = FastAPI(
    title="Open Notebook MCP Server",
    version="0.1.0",
    description="Provides MCP capabilities for Open Notebook.",
)

@app.on_event("startup")
async def load_tool_schemas():
    """Initialize tool registry by loading CLI commands"""
    try:
        inspector = CLIInspector()
        commands = inspector.load_commands_from_file("open_notebook_cli.py")
        tool_registry.load_tools(commands)
        logging.info(f"Successfully loaded {len(commands)} tools")
    except Exception as e:
        logging.error(f"Failed to load tool schemas: {str(e)}")
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
#     name: str
#     description: str | None = None
#
# @app.post("/notebooks/", status_code=201)
# async def create_notebook(notebook: NotebookCreate):
#     # Logic to create notebook, mirroring CLI
#     return {"id": "new_notebook_id", **notebook.model_dump()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)