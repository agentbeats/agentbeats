import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status

from ..db.storage import db
from ..a2a_client import a2a_client

router = APIRouter()

@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def register_agent(agent_info: Dict[str, Any]):
    """
    Register a new agent.
    NOTE: For local development/testing, you can set 'mock': True in the agent_info to bypass the agent card fetch.
    DO NOT USE THIS IN PRODUCTION. This is for mock/test data only!
    """
    try:
        # Validate required fields
        if 'name' not in agent_info or 'endpoint' not in agent_info or 'launcher' not in agent_info:
            raise HTTPException(status_code=400, detail="Missing required fields: name and endpoint")
        
        # --- MOCK AGENT REGISTRATION FOR TESTING ONLY ---
        # If 'mock' flag is set, skip the agent card fetch and use a dummy card.
        # This is for local development/testing and should NOT be used in production!
        if agent_info.get('mock'):
            # Dummy agent card structure (customize as needed for your frontend)
            agent_card = {
                "name": agent_info['name'],
                "type": agent_info.get('meta', {}).get('type', 'unknown'),
                "description": f"Mock agent card for {agent_info['name']} (testing only)",
                "mock": True
            }
        else:
            # --- PRODUCTION/REAL AGENT REGISTRATION ---
            # Fetch the agent card from the agent's endpoint (requires a real running agent)
            agent_card = await a2a_client.get_agent_card(agent_info['endpoint'])
            if not agent_card:
                raise HTTPException(status_code=400, detail="Failed to get agent card from endpoint")
        
        # Create agent record
        agent_record = {
            "registerInfo": agent_info,
            "agentCard": agent_card,
            "status": "unlocked",
            "ready": False
        }
        
        # Save to database
        created_agent = db.create("agents", agent_record)
        return created_agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering agent: {str(e)}")
        
@router.get("/agents")
def list_agents() -> List[Dict[str, Any]]:
    """List all agents."""
    try:
        agents = db.list("agents")
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing agents: {str(e)}")
        
@router.get("/agents/{agent_id}")
def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get a single agent by ID."""
    try:
        agent = db.read("agents", agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving agent: {str(e)}")

@router.put("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_agent(agent_id: str, update: Dict[str, Any]):
    """
    Update agent status or info.
    Request body can include 'ready': bool to indicate agent is ready after reset.
    """
    try:
        agent = db.read("agents", agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")

        # Update agent info based on request body
        if "ready" in update:
            agent["ready"] = bool(update["ready"])
        # You can add more fields to update here as needed

        db.update("agents", agent_id, agent)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")

@router.post("/mcp/agents/{agent_id}/card")
def update_agent_card(agent_id: str, card: Dict[str, Any]):
    """Update an agent's card."""
    try:
        agent = db.read("agents", agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
            
        # Update the agent card
        agent["agentCard"] = card
        db.update("agents", agent_id, agent)
        return None
    except HTTPException:
        raise
