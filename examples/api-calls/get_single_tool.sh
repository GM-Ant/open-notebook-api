#!/bin/bash
# Example: Get single tool by name with schema validation
TOOL_NAME="${1:-list-notebooks}"  # Default to 'list-notebooks' if no arg provided
API_URL="http://localhost:8000/tools/$TOOL_NAME"

response=$(curl -s -X GET "$API_URL")

# Validate response has required fields
if ! jq -e '.name and .description and .parameters' <<< "$response" >/dev/null; then
    echo "Error: Invalid tool schema format"
    echo "$response" | jq .
    exit 1
fi

# Print formatted response
echo "Successfully retrieved tool '$TOOL_NAME':"
echo "$response" | jq .