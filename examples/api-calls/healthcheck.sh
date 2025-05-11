#!/bin/bash
# Healthcheck verification script
API_URL="http://localhost:8000/health"

response=$(curl -s -X GET "$API_URL")

# Validate response structure
if ! jq -e '.status == "ok"' <<< "$response" >/dev/null; then
    echo "Error: Health check failed"
    echo "$response" | jq .
    exit 1
fi

echo "Health check successful:"
echo "$response" | jq .