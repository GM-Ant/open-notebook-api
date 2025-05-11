#!/bin/bash
# Example: Get all tools with schema validation
API_URL="http://localhost:8000/tools"

response=$(curl -s -X GET "$API_URL")

# Validate response is non-empty array
if ! jq -e '. | length > 0' <<< "$response" >/dev/null; then
    echo "Error: Invalid response format or empty tools list"
    echo "$response" | jq .
    exit 1
fi

# Print formatted response
echo "Successfully retrieved tools:"
echo "$response" | jq .