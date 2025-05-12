#!/bin/bash
# Test script for the MCP server integration

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "MCP Server Integration Test Script"
echo "=================================="

# Build the Docker image
echo -e "\nBuilding Docker image..."
docker build -t open_notebook_mcp:latest -f Dockerfile.mcp .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error: Docker build failed. Please check the output for errors.${NC}"
    exit 1
fi

# Get debug output from the container
echo -e "\\nRunning debug container to get diagnostic information..."
docker run --rm --name mcp_debug --env-file docker.env -e ENABLE_MCP_SERVER=true open_notebook_mcp:latest python /app/debug_mcp_imports.py > mcp_debug_output.log

echo -e "\\nDebug output saved to mcp_debug_output.log"
echo -e "Top 10 lines of debug output:"
head -n 10 mcp_debug_output.log
echo -e "..."

# Test 1: Check if the MCP server is running when enabled
echo -e "\\nTest 1: Checking if MCP server is running when enabled..."
docker run --rm -d --name mcp_test_enabled --env-file docker.env -p 8502:8502 -p 8001:8001 -e ENABLE_MCP_SERVER=true open_notebook_mcp:latest
sleep 15 # Wait for services to start

# Show container logs for debugging
echo -e "\nContainer logs (first 20 lines):"
docker logs mcp_test_enabled | head -n 20
echo -e "...\n"

# Check if the MCP server is responding
if curl -s http://localhost:8001/health | grep -q "status"; then
    echo -e "${GREEN}✓ Success: MCP server is running when enabled${NC}"
    
    # Show the tools available through the MCP server
    echo -e "\nTools available through MCP server:"
    curl -s http://localhost:8001/tools | jq '.[].name' 2>/dev/null || echo "Failed to get tools list"
else
    echo -e "${RED}✗ Failure: MCP server is not running when enabled${NC}"
    
    # Show more detailed logs if the test failed
    echo -e "\nDetailed container logs:"
    docker logs mcp_test_enabled
    
    # Try to connect to the container and debug
    echo -e "\\nAttempting to debug inside the container..."
    docker exec -it mcp_test_enabled bash -c "source /app/docker.env && cd /app && python debug_mcp_imports.py" || echo "Could not run debug script in container"
fi

# Stop the container
docker stop mcp_test_enabled

# Test 2: Check if the MCP server is NOT running when disabled
echo -e "\\nTest 2: Checking if MCP server is not running when disabled..."
docker run --rm -d --name mcp_test_disabled --env-file docker.env -p 8502:8502 -p 8001:8001 -e ENABLE_MCP_SERVER=false open_notebook_mcp:latest
sleep 10 # Wait for services to start

# Check if the MCP server is not responding
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Success: MCP server is not running when disabled${NC}"
else
    echo -e "${RED}✗ Failure: MCP server is running when it should be disabled${NC}"
fi

# Stop the container
docker stop mcp_test_disabled

# Test 3: Check if the notebook is still accessible when MCP server is enabled
echo -e "\\nTest 3: Checking if notebook is accessible when MCP server is enabled..."
docker run --rm -d --name mcp_test_notebook --env-file docker.env -p 8502:8502 -p 8001:8001 -e ENABLE_MCP_SERVER=true open_notebook_mcp:latest
sleep 10 # Wait for services to start

# Check if the notebook is responding
if curl -s http://localhost:8502 | grep -q "html"; then
    echo -e "${GREEN}✓ Success: Notebook is accessible when MCP server is enabled${NC}"
else
    echo -e "${RED}✗ Failure: Notebook is not accessible when MCP server is enabled${NC}"
fi

# Stop the container
docker stop mcp_test_notebook

# Print summary
echo -e "\nTest Summary"
echo -e "==============="
echo -e "The test script has completed. If any tests failed, check the logs above for details."
echo -e "You can also run a container interactively for debugging purposes:"
echo -e "docker run --rm -it --env-file docker.env -p 8502:8502 -p 8001:8001 -e ENABLE_MCP_SERVER=true open_notebook_mcp:latest bash"

# Test 4: Check if the CLI integration is working through the MCP server
echo -e "\nTest 4: Testing CLI integration through MCP server..."
# Get the list of tools exposed by the MCP server
TOOLS_RESPONSE=$(curl -s http://localhost:8001/tools)
if [[ $TOOLS_RESPONSE == *"\"name\""* ]]; then
    echo -e "${GREEN}✓ Success: MCP server tools endpoint is working${NC}"
    TOOL_COUNT=$(echo $TOOLS_RESPONSE | grep -o "\"name\"" | wc -l)
    echo "   Found $TOOL_COUNT tools"
else
    echo -e "${RED}✗ Failure: MCP server tools endpoint failed${NC}"
fi

# Test executing a tool through the MCP server
echo -e "\nTesting tool execution through MCP server..."
LIST_NOTEBOOKS_RESPONSE=$(curl -s -X POST http://localhost:8001/execute/list-notebooks \
  -H "Content-Type: application/json" \
  -d '{}')

if [[ $LIST_NOTEBOOKS_RESPONSE == *"\"status\":\"success\""* ]]; then
    echo -e "${GREEN}✓ Success: Successfully executed list-notebooks command through MCP server${NC}"
    echo "   Response: $LIST_NOTEBOOKS_RESPONSE"
else
    echo -e "${RED}✗ Failure: Failed to execute list-notebooks command${NC}"
    echo "   Response: $LIST_NOTEBOOKS_RESPONSE"
fi

# Stop the container
docker stop mcp_test_notebook

echo -e "\nTests completed."
