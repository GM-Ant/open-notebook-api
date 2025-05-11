#!/bin/bash
# Example error cases for tool API

# 1. Invalid tool name (404)
echo "Testing invalid tool name..."
curl -s -X GET "http://localhost:8000/tools/non-existent-tool" | jq .

# 2. Malformed tool name (400)
echo -e "\nTesting malformed tool name..."
curl -s -X GET "http://localhost:8000/tools/invalid!name" | jq .

# 3. Empty tool name (404)
echo -e "\nTesting empty tool name..."
curl -s -X GET "http://localhost:8000/tools/" | jq .

# 4. CLI command not found (404)
echo -e "\nTesting CLI command not found..."
curl -s -X POST "http://localhost:8000/cli" \
  -H "Content-Type: application/json" \
  -d '{"command": "non-existent-command", "args": {}}' | jq .

# 5. Invalid CLI input (400)
echo -e "\nTesting invalid CLI input..."
curl -s -X POST "http://localhost:8000/cli" \
  -H "Content-Type: application/json" \
  -d '{"command": "create-notebook", "args": {"description": "Missing name"}}' | jq .