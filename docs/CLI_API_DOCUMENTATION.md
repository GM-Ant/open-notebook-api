# Open Notebook CLI and API Documentation

This document provides detailed usage instructions for the Open Notebook Command Line Interface (CLI) and REST API.

## Table of Contents

- [Command Line Interface (CLI)](#command-line-interface-cli)
  - [Installation and Setup](#installation-and-setup)
  - [Common CLI Patterns](#common-cli-patterns)
  - [Notebook Commands](#notebook-commands)
  - [Source Commands](#source-commands)
  - [Note Commands](#note-commands)
  - [Transformation Commands](#transformation-commands)
  - [Chat Commands](#chat-commands)
  - [Search Commands](#search-commands)
  - [Podcast Commands](#podcast-commands)
  - [Help Commands](#help-commands)
  - [Error Handling](#cli-error-handling)
- [REST API](#rest-api)
  - [API Setup](#api-setup)
  - [Authentication](#authentication)
  - [API Endpoints](#api-endpoints)
    - [Health Check](#health-check)
    - [Command Execution](#command-execution)
  - [Request and Response Format](#request-and-response-format)
  - [Error Handling](#api-error-handling)
  - [Example API Calls](#example-api-calls)

## Command Line Interface (CLI)

The Open Notebook CLI provides a command-line interface for managing notebooks, sources, notes, transformations, and more.

### Installation and Setup

```bash
# Ensure Python package is installed
pip install open-notebook

# Alternative: Run the CLI script directly
python open_notebook_cli.py [command] [options]
```

### Common CLI Patterns

The CLI follows a consistent pattern for commands:

```bash
# General format
python open_notebook_cli.py <command> [arguments] [options]

# Notebook ID formats - for readability, you can prefix IDs with type
notebook:123   # Notebook with ID 123
src:456        # Source with ID 456
note:789       # Note with ID 789
```

### Notebook Commands

#### List Notebooks

```bash
# List all non-archived notebooks
python open_notebook_cli.py list-notebooks

# List all notebooks including archived ones
python open_notebook_cli.py list-notebooks --include-archived

# Order notebooks by a specific field
python open_notebook_cli.py list-notebooks --order-by "name asc"
python open_notebook_cli.py list-notebooks --order-by "created desc"
```

#### Get Notebook Details

```bash
python open_notebook_cli.py get-notebook notebook:123
```

#### Create Notebook

```bash
# Create a notebook with just a name
python open_notebook_cli.py create-notebook "My Research"

# Create a notebook with a name and description
python open_notebook_cli.py create-notebook "My Research" "Notes about my research project"
```

#### Archive/Unarchive Notebook

```bash
# Archive a notebook
python open_notebook_cli.py archive-notebook notebook:123

# Unarchive a notebook
python open_notebook_cli.py unarchive-notebook notebook:123
```

### Source Commands

#### List Sources

```bash
# List all sources in a notebook
python open_notebook_cli.py list-sources notebook:123
```

#### Get Source Details

```bash
# Get basic source information
python open_notebook_cli.py get-source src:456

# Include full text in the result
python open_notebook_cli.py get-source src:456 --full-text

# Include insights generated for this source
python open_notebook_cli.py get-source src:456 --show-insights
```

#### Add Text Source

```bash
# Add a basic text source to a notebook
python open_notebook_cli.py add-text-source notebook:123 "My Source" "This is the content of my source"

# Add a text source and generate embeddings for semantic search
python open_notebook_cli.py add-text-source notebook:123 "My Source" "This is the content of my source" --embed

# Add a text source and apply standard transformations
python open_notebook_cli.py add-text-source notebook:123 "My Source" "This is the content of my source" --transform

# Add a text source and apply specific transformations
python open_notebook_cli.py add-text-source notebook:123 "My Source" "This is the content of my source" --apply-transformations trans:111 trans:222
```

#### Add URL Source

```bash
# Add a URL source to a notebook
python open_notebook_cli.py add-url-source notebook:123 "https://example.com/article"

# Add a URL source with embeddings and transformations
python open_notebook_cli.py add-url-source notebook:123 "https://example.com/article" --embed --transform
```

#### Embed Source

```bash
# Generate embeddings for semantic search
python open_notebook_cli.py embed-source src:456
```

### Note Commands

#### List Notes

```bash
# List all notes in a notebook
python open_notebook_cli.py list-notes notebook:123
```

#### Get Note Details

```bash
python open_notebook_cli.py get-note note:789
```

#### Create Note

```bash
# Create a human-authored note
python open_notebook_cli.py create-note notebook:123 "My Note" "This is the content of my note"

# Create an AI-generated note
python open_notebook_cli.py create-note notebook:123 "AI Summary" "This is an AI-generated summary" --type ai
```

#### Convert Source Insight to Note

```bash
python open_notebook_cli.py insight-to-note ins:111 notebook:123
```

### Transformation Commands

#### List Transformations

```bash
python open_notebook_cli.py list-transformations
```

#### Get Transformation Details

```bash
python open_notebook_cli.py get-transformation trans:111
```

#### Create Transformation

```bash
python open_notebook_cli.py create-transformation "Summary" "sum" "Creates a summary of the source" "Summarize: {{text}}"

# Create a transformation that is applied by default to new sources
python open_notebook_cli.py create-transformation "Summary" "sum" "Creates a summary of the source" "Summarize: {{text}}" --apply-default
```

#### Apply Transformation

```bash
# Apply a specific transformation to a source
python open_notebook_cli.py apply-transformation src:456 trans:111

# Apply standard transformations to a source
python open_notebook_cli.py apply-transformation src:456 --transform
```

### Chat Commands

#### List Chat Sessions

```bash
python open_notebook_cli.py list-chat-sessions notebook:123
```

#### Create Chat Session

```bash
python open_notebook_cli.py create-chat-session notebook:123 "Research Discussion"
```

### Search Commands

#### Text Search

```bash
# Basic text search across sources and notes
python open_notebook_cli.py text-search "machine learning"

# Limit number of results
python open_notebook_cli.py text-search "machine learning" --results 5

# Search only in sources
python open_notebook_cli.py text-search "machine learning" --source --no-note

# Search only in notes
python open_notebook_cli.py text-search "machine learning" --note --no-source
```

#### Vector Search (Semantic Search)

```bash
# Basic semantic search
python open_notebook_cli.py vector-search "How does machine learning work?"

# Advanced semantic search with options
python open_notebook_cli.py vector-search "How does machine learning work?" --results 10 --min-score 0.5 --source --no-note
```

### Podcast Commands

#### List Podcast Templates

```bash
python open_notebook_cli.py list-podcast-templates
```

#### Get Podcast Template

```bash
python open_notebook_cli.py get-podcast-template ptmpl:111
```

#### List Podcast Episodes

```bash
python open_notebook_cli.py list-podcast-episodes

# Order episodes
python open_notebook_cli.py list-podcast-episodes --order-by "created desc"
```

#### Generate Podcast

```bash
# Basic podcast generation
python open_notebook_cli.py generate-podcast ptmpl:111 notebook:123 "Episode Title"

# With additional options
python open_notebook_cli.py generate-podcast ptmpl:111 notebook:123 "Episode Title" --instructions "Focus on AI topics" --longform
```

### Help Commands

```bash
# Get general CLI help
python open_notebook_cli.py --help

# Get help for a specific command
python open_notebook_cli.py get-command-help list-notebooks
```

### CLI Error Handling

The CLI can generate the following types of errors:

1. **CLINotFoundException** - When a requested resource (notebook, source, note, etc.) is not found
   ```
   Error: Notebook not found: notebook:xyz
   ```

2. **CLIInvalidInputException** - When the provided input is invalid
   ```
   Error: Notebook name cannot be empty.
   ```

3. **CLIExecutionException** - When there's an error during command execution
   ```
   Error: Database error while creating notebook: [details]
   ```

## REST API

The Open Notebook REST API provides a HTTP interface for executing the same commands available in the CLI. It's ideal for integrating Open Notebook with other systems or building custom interfaces.

### API Setup

The API is built with FastAPI and can be launched as follows:

```bash
# Install required dependencies
pip install open-notebook[api]  # Includes FastAPI and Uvicorn

# Launch the API server
uvicorn api_main:app --host 0.0.0.0 --port 8000
```

### Authentication

The current implementation does not include authentication. In production, consider adding authentication using FastAPI security utilities.

### API Endpoints

#### Health Check

Check if the API is functioning correctly.

- **URL**: `/health`
- **Method**: `GET`
- **Response Example**:
  ```json
  {
    "status": "ok",
    "message": "API is running"
  }
  ```

#### Command Execution

Execute any Open Notebook CLI command via the API.

- **URL**: `/cli`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "command": "string",
    "args": {
      "key1": "value1",
      "key2": "value2"
    }
  }
  ```

### Request and Response Format

The API accepts and returns JSON data. When calling the `/cli` endpoint:

- **command**: The name of the CLI command to execute (e.g., "list-notebooks")
- **args**: A dictionary containing command arguments
  - For CLI flags like `--include-archived`, use `{"include_archived": true}`
  - For positional arguments, use named keys matching the CLI argument names

The API always returns a JSON response with the command result or error details.

### API Error Handling

The API returns standard HTTP status codes:

- **200**: Command executed successfully
- **400**: Bad request (invalid input or command)
- **404**: Resource not found
- **500**: Server error

Error responses include a `detail` field with the error message:

```json
{
  "detail": "Notebook not found: notebook:xyz"
}
```

### Example API Calls

#### List Notebooks

```bash
curl -X POST http://localhost:8000/cli \
  -H "Content-Type: application/json" \
  -d '{
    "command": "list-notebooks",
    "args": {
      "include_archived": true,
      "order_by": "created desc"
    }
  }'
```

#### Create Notebook

```bash
curl -X POST http://localhost:8000/cli \
  -H "Content-Type: application/json" \
  -d '{
    "command": "create-notebook",
    "args": {
      "name": "My Research",
      "description": "Notes about my research project"
    }
  }'
```

#### Add Text Source

```bash
curl -X POST http://localhost:8000/cli \
  -H "Content-Type: application/json" \
  -d '{
    "command": "add-text-source",
    "args": {
      "notebook_id": "notebook:123",
      "title": "My Source",
      "content": "This is the content of my source",
      "embed": true,
      "transform": true
    }
  }'
```

#### Search

```bash
curl -X POST http://localhost:8000/cli \
  -H "Content-Type: application/json" \
  -d '{
    "command": "vector-search",
    "args": {
      "query": "How does machine learning work?",
      "results": 5,
      "min_score": 0.3,
      "source": true,
      "note": true
    }
  }'
```

#### Generate Podcast

```bash
curl -X POST http://localhost:8000/cli \
  -H "Content-Type: application/json" \
  -d '{
    "command": "generate-podcast",
    "args": {
      "template_id": "ptmpl:111",
      "notebook_id": "notebook:123",
      "episode_name": "Machine Learning Basics",
      "instructions": "Focus on beginner concepts",
      "longform": true
    }
  }'
```
