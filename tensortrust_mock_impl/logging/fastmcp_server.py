# server.py
import datetime
from mcp.server.fastmcp import FastMCP
import uvicorn
from fastapi import FastAPI

# Real agent IDs from agents.json
GREEN_AGENT_ID = "aa391b87-8bb8-4ad0-bc8b-3504454fb36b"
BLUE_AGENT_ID = "835f9a09-ca07-4360-be93-81c6d6bd1cc1"
RED_AGENT_ID = "77ff16db-835a-4f95-b9e3-652840cb0958"

# In-memory mapping from logical battle_id to backend battle_id
BATTLE_ID_MAP = {}

# Create an MCP server
mcp = FastMCP("fastmcp-logger", 
                host="0.0.0.0",
                port=11000)

# Add a tool to update battle results via backend API
@mcp.tool()
def update_battle_result(battle_id: str, result: dict) -> str:
    """Update battle results in the backend database via API call"""
    import requests
    import json
    global BATTLE_ID_MAP
    
    try:
        # Use mapped backend battle id if available
        backend_battle_id = BATTLE_ID_MAP.get(battle_id, battle_id)
        # First, try to get the battle to see if it exists
        get_response = requests.get(f"http://localhost:3001/battles/{backend_battle_id}")
        
        if get_response.status_code == 404:
            # Battle doesn't exist, create a battle with the correct agent IDs
            create_data = {
                "greenAgentId": GREEN_AGENT_ID,
                "opponents": [BLUE_AGENT_ID, RED_AGENT_ID],
                "config": {"timeout": 300}
            }
            
            create_response = requests.post(
                "http://localhost:3001/battles",
                json=create_data,
                headers={"Content-Type": "application/json"}
            )
            
            if create_response.status_code != 201:
                return f"Failed to create battle: {create_response.status_code} - {create_response.text}"
            # Use the backend-generated battle ID for updates
            backend_battle_id = create_response.json().get("id")
            if not backend_battle_id:
                return f"Battle created but no ID returned by backend."
            # Store the mapping for future updates
            BATTLE_ID_MAP[battle_id] = backend_battle_id
        else:
            # If the mapping was not set before, set it now
            if battle_id not in BATTLE_ID_MAP and backend_battle_id != battle_id:
                BATTLE_ID_MAP[battle_id] = backend_battle_id
        
        # Now update the battle result
        response = requests.post(
            f"http://localhost:3001/battles/{backend_battle_id}",
            json=result,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 204:
            return f"Successfully updated battle result for battle {backend_battle_id}"
        else:
            return f"Failed to update battle result: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error updating battle result: {str(e)}"

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run(transport="sse")