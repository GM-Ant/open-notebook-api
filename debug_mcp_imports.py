# filepath: /Users/gregory/localcode/open-notebook/debug_mcp_imports.py
import os
import sys

print("--- MCP Debug Import Script ---")
print(f"Python version: {sys.version}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")

# Print relevant environment variables
print("\n--- Environment Variables ---")
RELEVANT_VARS = [
    "SURREAL_ADDRESS", "SURREAL_USER", "SURREAL_PASSWORD",
    "SURREAL_NAMESPACE", "SURREAL_DATABASE", "ENABLE_MCP_SERVER",
    "MCP_SERVER_PORT"
]
for var in RELEVANT_VARS:
    print(f"{var}: {os.environ.get(var)}")

print("\n--- Attempting Imports ---")
try:
    from open_notebook.database import repository
    print("[SUCCESS] Imported open_notebook.database.repository")

    # Attempt to instantiate or use the repository to trigger env var checks
    # This depends on how repository.py is structured.
    # If SurrealRepository is a class that takes config from env vars in __init__:
    if hasattr(repository, 'SurrealRepository'):
        print("Attempting to instantiate SurrealRepository...")
        repo_instance = repository.SurrealRepository()
        print("[SUCCESS] Instantiated SurrealRepository.")
        # You might want to call a connect method if it exists and is separate
        # if hasattr(repo_instance, 'connect'):
        #     print("Attempting to connect...")
        #     repo_instance.connect() # This might raise the KeyError if not handled
        #     print("[SUCCESS] Connection method called.")
    else:
        print("[INFO] SurrealRepository class not found directly under repository module. Initialization check might be different.")

except ImportError as e:
    print(f"[ERROR] ImportError: {e}")
    print("Please check PYTHONPATH and ensure the package is installed correctly.")
except KeyError as e:
    print(f"[ERROR] KeyError: {e}")
    print("This usually means a required environment variable for database connection is missing.")
    print("Please ensure all SURREAL_* environment variables are set correctly when running the container.")
except Exception as e:
    print(f"[ERROR] An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()
else:
    print("\n--- Imports and Initial Checks Potentially Successful ---")

print("\n--- MCP Debug Script Finished ---")
