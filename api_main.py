\
from fastapi import FastAPI, HTTPException, Body, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
import logging
import sys
import os
from argparse import Namespace

# Attempt to import the CLI class and necessary setup functions
# This assumes 'open_notebook_cli.py' is in the PYTHONPATH or same directory,
# and has been refactored as discussed (e.g., if __name__ == "__main__" block).
try:
    from open_notebook_cli import OpenNotebookCLI
    from open_notebook.tool_reflector import CLIInspector  # Import for Phase 2 integration
    # If your CLI or its underlying models need explicit initialization (e.g., DB connection):
    # from open_notebook.config import load_config
    # from open_notebook.database.repository import init_db_from_config
    # load_config() # Example: Load global configuration
    # init_db_from_config() # Example: Initialize database
    cli_instance = OpenNotebookCLI()
    # It's crucial that cli_instance.parser is populated, e.g., in OpenNotebookCLI.__init__
    # by calling self.parser = self._create_parser()
except ImportError as e:
    logging.error(f"Failed to import or initialize OpenNotebookCLI: {e}. API will not function correctly.")
    cli_instance = None
except Exception as e:
    logging.error(f"An unexpected error occurred during OpenNotebookCLI initialization: {e}")
    cli_instance = None

# Define custom exceptions that might be raised by the refactored CLI
class CLIBaseException(Exception):
    pass

class CLINotFoundException(CLIBaseException): # For things like NotebookNotFound
    pass

class CLIInvalidInputException(CLIBaseException): # For bad arguments
    pass


app = FastAPI(
    title="Open Notebook CLI API",
    description="API interface for the OpenNotebook CLI tool. Allows executing CLI commands via HTTP.",
    version="1.0.0"
)

# Setup basic logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CLICommandPayload(BaseModel):
    command: str = Field(..., description="The CLI command to execute (e.g., 'list-notebooks', 'create-notebook').")
    args: Optional[Dict[str, Any]] = Field(default_factory=dict, description="A dictionary of arguments for the command. For flags, use true/false (e.g., {'include-archived': true}). For arguments with values, use key-value pairs (e.g., {'notebook_id': 'xyz', 'name': 'My Notebook'}). Positional arguments should also be named if the CLI method expects them as named attributes on the 'args' object.")

def get_cli_instance():
    if not cli_instance:
        logger.error("OpenNotebookCLI instance is not available.")
        raise HTTPException(status_code=503, detail="CLI service is not available. Check server logs for import errors.")
    if not hasattr(cli_instance, 'parser') or not cli_instance.parser:
        logger.error("OpenNotebookCLI parser is not initialized.")
        raise HTTPException(status_code=503, detail="CLI parser is not initialized. Check server logs.")
    return cli_instance

@app.post("/cli",
          summary="Execute an OpenNotebook CLI command",
          response_description="The result of the CLI command, typically JSON.")
async def execute_cli_command(payload: CLICommandPayload, current_cli: OpenNotebookCLI = Depends(get_cli_instance)):
    """
    Executes a specified OpenNotebook CLI command with the given arguments.

    - **command**: The name of the command (e.g., `list-notebooks`).
    - **args**: A dictionary of arguments.
        - For flags like `--include-archived`, use `{"include-archived": true}`.
        - For options with values like `--order-by "created desc"`, use `{"order-by": "created desc"}`.
        - For positional arguments like `create-notebook <name> <description>`, if your CLI handler
          expects them as `args.name` and `args.description`, provide them as `{"name": "My Name", "description": "My Desc"}`.
          The API layer currently does not reconstruct exact positional vs. optional args for the underlying `argparse`
          but rather creates a Namespace object. Ensure your CLI methods (after refactoring) can handle this,
          perhaps using `getattr(args, 'param_name', default_value)`.
    """
    logger.info(f"Received CLI command: {payload.command} with args: {payload.args}")

    method_name = payload.command.replace('-', '_')
    if not hasattr(current_cli, method_name):
        logger.warning(f"Command '{payload.command}' not found in CLI instance.")
        raise HTTPException(status_code=400, detail=f"Command '{payload.command}' not found.")

    cli_method = getattr(current_cli, method_name)

    # Construct a Namespace-like object for the CLI method.
    # CLI methods should be refactored to use getattr(args, 'attr_name', default_value)
    # for optional arguments to handle cases where they are not provided.
    # The API will always inject 'json': True.
    processed_args_dict = payload.args.copy()
    processed_args_dict['json'] = True  # API always expects JSON response from CLI logic

    # Convert snake_case keys from payload.args to kebab-case if your CLI parser expects that for some reason,
    # or ensure your CLI methods handle attributes named as per payload.args keys.
    # For simplicity, we assume payload.args keys match attribute names expected by CLI methods (e.g. notebook_id, include_archived)
    cli_method_args = Namespace(**processed_args_dict)

    try:
        logger.debug(f"Calling CLI method: {method_name} with Namespace: {cli_method_args}")
        result = cli_method(cli_method_args)
        logger.info(f"Command '{payload.command}' executed successfully.")
        return result
    except CLINotFoundException as e: # Custom exception from refactored CLI
        logger.warning(f"Resource not found for command '{payload.command}': {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except CLIInvalidInputException as e: # Custom exception from refactored CLI
        logger.warning(f"Invalid input for command '{payload.command}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e: # Catch generic ValueErrors as bad requests
        logger.warning(f"ValueError during command '{payload.command}': {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except TypeError as e: # Catch generic TypeErrors (e.g. missing required arg not handled by getattr)
        logger.warning(f"TypeError during command '{payload.command}': {e}")
        raise HTTPException(status_code=400, detail=f"Type error or missing argument: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error executing command '{payload.command}': {e}", exc_info=True)
        # Consider if this is a client error (4xx) or server error (5xx)
        # For unhandled CLI exceptions, 500 is safer.
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health",
         summary="Health check",
         response_description="API health status.")
async def health_check():
    """
    Provides a simple health check for the API.
    Returns `{"status": "ok"}` if the API is running.
    """
    # Could add checks for CLI instance availability if desired
    # if not cli_instance or not hasattr(cli_instance, 'parser'):
    #    return {"status": "degraded", "message": "CLI backend not fully initialized."}
    return {"status": "ok", "message": "API is running"}

# To run this app (save as api_main.py):
# uvicorn api_main:app --reload
#
# Remember to implement the custom exceptions (CLINotFoundException, etc.) in your
# open_notebook_cli.py or a shared exceptions module, and raise them from CLI methods.
