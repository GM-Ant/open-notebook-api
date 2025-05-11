from fastapi import FastAPI, HTTPException
from open_notebook.tool_registry import tool_registry

app = FastAPI(
    title="Open Notebook MCP Server",
    version="0.1.0",
    description="Provides MCP capabilities for Open Notebook.",
)

@app.on_event("startup")
async def startup_event():
    """Initialize the tool registry on application startup"""
    tool_registry.load_tools()

@app.get("/")
async def read_root():
    return {"message": "Open Notebook MCP Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

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