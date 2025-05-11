# MCP Server Scaffolding Plan

This document outlines the plan for creating the initial Poetry-based project scaffolding for the Open Notebook MCP server.

## Proposed Plan

**Phase 1: Project Scaffolding and Initial File Creation (Architect Mode)**

1.  **Create Project Directory:**
    *   Create the main package directory: `open_notebook_mcp/` (located at `/Users/gregory/localcode/open-notebook/open_notebook_mcp/`).

2.  **Create `pyproject.toml`:**
    *   Create the file `open_notebook_mcp/pyproject.toml` with the exact content:
        ```toml
        [tool.poetry]
        name = "open-notebook-mcp"
        version = "0.1.0"
        description = "MCP Server for Open Notebook"
        authors = ["Your Name <you@example.com>"]

        [tool.poetry.dependencies]
        python = "^3.11"
        fastapi = "^0.109.0"
        uvicorn = {extras = ["standard"], version = "^0.27.0"}
        pydantic = "^2.6.0"
        open-notebook = {path = "../", develop = true}

        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"
        ```

3.  **Create `main.py` (FastAPI Entrypoint):**
    *   Create the file `open_notebook_mcp/main.py` with the following content:
        ```python
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
        ```

4.  **Create `Dockerfile`:**
    *   Create the file `open_notebook_mcp/Dockerfile` with the following content:
        ```dockerfile
        # Stage 1: Build the application
        FROM python:3.11-slim as builder

        # Set working directory
        WORKDIR /app

        # Install poetry
        RUN pip install poetry

        # Copy only files necessary for dependency installation
        COPY pyproject.toml poetry.lock* ./

        # Install production dependencies
        # --no-dev: Do not install development dependencies
        # --no-interaction: Do not ask any interactive questions
        # --no-ansi: Disable ANSI output
        RUN poetry install --no-dev --no-interaction --no-ansi

        # Copy the rest of the application code
        COPY . .

        # Stage 2: Production image
        FROM python:3.11-slim

        WORKDIR /app

        # Set environment variables
        ENV PYTHONUNBUFFERED=1 \
            APP_ENV=production \
            PORT=8000

        # Copy installed dependencies from builder stage
        COPY --from=builder /app/.venv /.venv
        # Copy application code
        COPY --from=builder /app/main.py ./main.py
        # If you have other source files under open_notebook_mcp, copy them too
        # COPY --from=builder /app/open_notebook_mcp ./open_notebook_mcp

        # Activate virtual environment
        ENV PATH="/app/.venv/bin:$PATH"

        # Expose the port the app runs on
        EXPOSE 8000

        # Healthcheck
        HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
          CMD curl -f http://localhost:8000/health || exit 1

        # Command to run the application
        CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
        ```

**Phase 2: Implementation (To be performed in "Code" mode)**

*   **Step 2.1: Initialize Poetry and Install Dependencies:**
    *   The "Code" mode will navigate to the `open_notebook_mcp/` directory.
    *   Execute `poetry install` (this will also generate `poetry.lock` if it doesn't exist based on `pyproject.toml`).
*   **Step 2.2: Docker Build Verification:**
    *   The "Code" mode will execute `docker build -t mcp .` within the `open_notebook_mcp/` directory.
*   **Step 2.3: Git Commit and Changelog:**
    *   The "Code" mode will:
        *   Add all new files in `open_notebook_mcp/` to git.
        *   Commit the changes with a message like "feat: Initial scaffolding for MCP server".
        *   Obtain the commit hash.
        *   Prepare a changelog entry (e.g., "Added initial project scaffolding for the Open Notebook MCP server, including FastAPI setup, Dockerfile, and Poetry configuration.").

## Visual Plan (Mermaid Diagram)

```mermaid
graph TD
    A[Start: Task Received] --> B{Understand Requirements};
    B -- CLI Parity & Dir Structure Confirmed --> C[Phase 1: Architect Mode - Scaffolding Definition];
    C --> C1[Define dir: open_notebook_mcp/];
    C1 --> C2[Define file: open_notebook_mcp/pyproject.toml];
    C2 --> C3[Define file: open_notebook_mcp/main.py];
    C3 --> C4[Define file: open_notebook_mcp/Dockerfile];
    C4 --> D{Review Plan with User};
    D -- Approved --> E[Offer to Save Plan to Markdown];
    E --> F[Switch to Code Mode for Implementation];

    subgraph Phase 2: Code Mode - Implementation
        direction LR
        F1[cd open_notebook_mcp/]
        F1 --> G[poetry install]
        G --> H[docker build -t mcp .]
        H --> I[Git Add & Commit]
        I --> J[Generate Changelog Entry & Get Commit Hash]
    end

    F --> F1;
    J --> K[End: Deliverables Provided];