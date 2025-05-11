from fastapi import FastAPI

app = FastAPI(
    title="Open Notebook MCP Server",
    version="0.1.0",
    description="Provides MCP capabilities for Open Notebook.",
)

@app.get("/")
async def read_root():
    return {"message": "Open Notebook MCP Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Placeholder for future CLI parity endpoints
# Example:
# from pydantic import BaseModel
# class NotebookCreate(BaseModel):
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