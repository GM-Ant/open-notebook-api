\
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Attempt to import the FastAPI app and the CLI class
# This assumes api_main.py and open_notebook_cli.py are in the python path
# For a real setup, you might need to adjust sys.path or use a proper package structure
try:
    from api_main import app  # Assuming your FastAPI app instance is named 'app'
    from open_notebook_cli import OpenNotebookCLI, CLINotFoundException, CLIInvalidInputException, CLIExecutionException
except ImportError as e:
    print(f"Error importing modules for testing: {e}")
    print("Please ensure api_main.py and open_notebook_cli.py are accessible.")
    # Define dummy classes if import fails, so tests can be discovered
    class OpenNotebookCLI:
        def __init__(self, *args, **kwargs):
            pass
        def run_command(self, *args, **kwargs):
            return {} # Default mock behavior
    
    class CLINotFoundException(Exception): pass
    class CLIInvalidInputException(Exception): pass
    class CLIExecutionException(Exception): pass

    # Dummy FastAPI app for TestClient
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/health")
    async def health_check_dummy():
        return {"status": "ok"}

    @app.post("/cli")
    async def cli_dummy(payload: dict):
        return {"error": "CLI not loaded"}, 500

client = TestClient(app)

@pytest.fixture
def mock_cli_runner():
    # This fixture provides a mock for the OpenNotebookCLI instance's run_command method
    # It will be used by the API endpoint.
    mock_runner = MagicMock(spec=OpenNotebookCLI)
    return mock_runner

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Patch the 'cli_instance' in api_main where OpenNotebookCLI is instantiated and used.
# The exact path to patch depends on how 'cli_instance' is defined and used in 'api_main.py'.
# Example: @patch('api_main.cli_instance.run_command') if cli_instance is a global object
# Or, if OpenNotebookCLI is instantiated per request: @patch('api_main.OpenNotebookCLI')
# For this example, let's assume OpenNotebookCLI is instantiated inside the endpoint or is a dependency.
# A more robust way is to use FastAPI's dependency overrides for testing.

# For simplicity, let's assume api_main.py has a global cli_instance or similar
# that the /cli endpoint uses. If not, dependency injection is preferred.
# This example will mock the run_command method directly on the class,
# which might not be ideal if instances are created per call without DI.

@patch('open_notebook_cli.OpenNotebookCLI.run_command')
def test_cli_post_success(mock_run_command):
    mock_run_command.return_value = {"id": "notebook:123", "name": "Test Notebook"}
    
    payload = {
        "command": "create-notebook",
        "args": {"name": "Test Notebook", "description": "A test notebook"}
    }
    response = client.post("/cli", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"id": "notebook:123", "name": "Test Notebook"}
    mock_run_command.assert_called_once()
    # Further assertions can be made on the arguments passed to mock_run_command

@patch('open_notebook_cli.OpenNotebookCLI.run_command')
def test_cli_post_command_not_found(mock_run_command):
    mock_run_command.side_effect = CLINotFoundException("Command foobar not found")
    
    payload = {
        "command": "foobar",
        "args": {}
    }
    response = client.post("/cli", json=payload)
    
    assert response.status_code == 404
    assert "Command foobar not found" in response.json()["detail"]

@patch('open_notebook_cli.OpenNotebookCLI.run_command')
def test_cli_post_invalid_input(mock_run_command):
    mock_run_command.side_effect = CLIInvalidInputException("Missing required argument: name")
    
    payload = {
        "command": "create-notebook",
        "args": {"description": "A test notebook without a name"} # Missing 'name'
    }
    response = client.post("/cli", json=payload)
    
    assert response.status_code == 400 # Or 422 if Pydantic validation catches it first
    assert "Missing required argument: name" in response.json()["detail"]

@patch('open_notebook_cli.OpenNotebookCLI.run_command')
def test_cli_post_execution_error(mock_run_command):
    mock_run_command.side_effect = CLIExecutionException("Database connection failed")
    
    payload = {
        "command": "list-notebooks",
        "args": {}
    }
    response = client.post("/cli", json=payload)
    
    assert response.status_code == 500
    assert "Database connection failed" in response.json()["detail"]

def test_cli_post_bad_payload_missing_command():
    payload = {
        # "command": "list-notebooks", # Missing command
        "args": {}
    }
    response = client.post("/cli", json=payload)
    assert response.status_code == 422 # FastAPI's unprocessable entity for Pydantic errors

def test_cli_post_bad_payload_missing_args():
    payload = {
        "command": "list-notebooks"
        # "args": {} # Missing args
    }
    response = client.post("/cli", json=payload)
    assert response.status_code == 422

# Example of testing a specific CLI command's logic if you were testing the CLI directly (not via API)
@patch('open_notebook_cli.Notebook') # Mocking the Domain Model
def test_cli_create_notebook_direct(MockNotebookModel):
    # This is more of a unit test for OpenNotebookCLI itself
    cli = OpenNotebookCLI()
    
    # Mock the save method and ID generation for the Notebook model
    mock_notebook_instance = MagicMock()
    mock_notebook_instance.id = "notebook:xyz123"
    mock_notebook_instance.name = "My Test Notebook"
    mock_notebook_instance.description = "A description"
    mock_notebook_instance.created = "2023-01-01T12:00:00" # Example datetime string
    
    MockNotebookModel.return_value = mock_notebook_instance # When Notebook() is called
    
    # Simulate parsed args
    class Args:
        pass
    args = Args()
    args.name = "My Test Notebook"
    args.description = "A description"
    args.json = True # Important for return type

    result = cli.create_notebook(args) # Call the method directly

    MockNotebookModel.assert_called_once_with(name="My Test Notebook", description="A description")
    mock_notebook_instance.save.assert_called_once()
    
    assert result["id"] == "notebook:xyz123"
    assert result["name"] == "My Test Notebook"

# Add more tests for other commands and edge cases for the CLI class itself if needed.
# The tests above primarily focus on the API layer and its interaction with the CLI.
