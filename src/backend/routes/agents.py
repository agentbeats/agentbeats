import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal
from agents import Agent, Runner

from ..db.storage import db
from ..a2a_client import a2a_client

router = APIRouter()


@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def register_agent(agent_info: Dict[str, Any]):
    """Register a new agent."""
    try:
        # Validate required fields
        if (
            "alias" not in agent_info
            or "agent_url" not in agent_info
            or "launcher_url" not in agent_info
            or "is_green" not in agent_info
            # or "roles" not in agent_info
        ):
            raise HTTPException(
                status_code=400, detail="Missing required fields: alias, agent_url, launcher_url, is_green, roles"
            )

        if not isinstance(agent_info.get("is_green"), bool):
            raise HTTPException(
                status_code=400, detail="is_green must be a boolean value"
            )

        # # Validate roles field
        # if not isinstance(agent_info["roles"], dict):
        #     raise HTTPException(
        #         status_code=400, detail="roles must be a dictionary mapping agent IDs to role info"
        #     )

        # Green agent must provide participant_requirements
        if agent_info["is_green"] and "participant_requirements" not in agent_info:
            raise HTTPException(
                status_code=400,
                detail="Green agents must provide participant_requirements",
            )

        # Check if each requirement is valid
        for req in agent_info.get("participant_requirements", []):
            if (
                not isinstance(req, dict)
                or "role" not in req
                or "name" not in req
                or "required" not in req
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Each participant requirement must be a dict with 'role' and 'name' and 'required' fields",
                )

        # Get agent card from the agent_url
        agent_card = await a2a_client.get_agent_card(agent_info["agent_url"])
        if not agent_card:
            raise HTTPException(
                status_code=400, detail="Failed to get agent card from agent_url"
            )

        # Create agent record
        elo_rating = None if agent_info.get("is_green") else 1000
        agent_record = {
            "register_info": agent_info,
            "agent_card": agent_card,
            "status": "unlocked",
            "ready": False,
            "elo": {
                "rating": elo_rating,
                "battle_history": [],
                "stats": {
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "errors": 0,
                    "total_battles": 0,
                    "win_rate": 0.0,
                    "loss_rate": 0.0,
                    "draw_rate": 0.0,
                    "error_rate": 0.0
                }
            }
        }

        # Save to database
        created_agent = db.create("agents", agent_record)
        return created_agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error registering agent: {str(e)}"
        )


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
            raise HTTPException(
                status_code=404, detail=f"Agent with ID {agent_id} not found"
            )
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
            raise HTTPException(
                status_code=404, detail=f"Agent with ID {agent_id} not found"
            )

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
            raise HTTPException(
                status_code=404, detail=f"Agent with ID {agent_id} not found"
            )

        # Update the agent card
        agent["agent_card"] = card
        db.update("agents", agent_id, agent)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating agent card: {str(e)}"
        )


@router.post("/agents/card")
async def get_agent_card(request: Dict[str, Any]):
    """Get agent card from agent URL via backend proxy to avoid CORS issues."""
    try:
        if "agent_url" not in request:
            raise HTTPException(
                status_code=400, detail="Missing required field: agent_url"
            )

        agent_url = request["agent_url"]
        if not agent_url:
            raise HTTPException(status_code=400, detail="agent_url cannot be empty")

        # Get agent card from the agent_url using a2a_client
        agent_card = await a2a_client.get_agent_card(agent_url)
        if not agent_card:
            raise HTTPException(
                status_code=400, detail="Failed to get agent card from agent_url"
            )

        return agent_card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting agent card: {str(e)}"
        )


ANALYZE_PROMPT = """
You are an expert system for analyzing agent cards in a multi-agent battle framework.
Given a JSON object representing an agent card, identify:
1. Whether this agent is likely to be a "green agent" (i.e. judge or coordinator).
2. If it is a green agent, what participant requirements should be set based on its skills or description. 'role' can be 'red_agent', 'blue_agent', etc. 'red_agent' is the attacker, 'blue_agent' is the defender. 'name' should be a simple agent name in underscore format (e.g., 'prompt_injector', 'defense_agent'). 'required' should be true if the agent is mandatory for the battle, false otherwise.
3. If it is a green agent, analyze the battle timeout, if it is in the agent card, otherwise default to 300 seconds.
"""


class ParticipantRequirement(BaseModel):
    role: Literal["red_agent", "blue_agent"]
    
    name: str
    "Simple agent name in underscore format (e.g., 'prompt_injector', 'defense_agent'). AVOID descriptive suffixes, make it simple."
    
    required: bool


class AnalyzeResult(BaseModel):
    is_green: bool
    "Whether the agent is a green agent (i.e. judge or coordinator)",

    participant_requirements: list[ParticipantRequirement]
    "List of participant requirements for the participant agents.",

    battle_timeout: int
    "Battle timeout in seconds. If not specified in the agent card, default to 300 seconds.",


@router.post("/agents/analyze_card")
async def analyze_agent_card(request: Dict[str, Any]):
    """Analyze agent card using LLM to suggest agent type and requirements."""
    try:
        if "agent_card" not in request:
            raise HTTPException(
                status_code=400, detail="Missing required field: agent_card"
            )

        agent_card = request["agent_card"]
        if not agent_card:
            raise HTTPException(status_code=400, detail="agent_card cannot be empty")

        analyze_agent = Agent(
            name="Agent Card Analyzer",
            instructions=ANALYZE_PROMPT,
            output_type=AnalyzeResult,
            model="gpt-4o",
        )

        response = await Runner.run(
            analyze_agent,
            input=str(agent_card),
        )

        analysis_result = response.final_output_as(AnalyzeResult)

        participant_requirements_list = []
        for req in analysis_result.participant_requirements:
            participant_requirements_list.append(
                {
                    "role": req.role,
                    "name": req.name,
                    "required": req.required,
                }
            )

        analysis_result = {
            "is_green": analysis_result.is_green,
            "participant_requirements": participant_requirements_list,
            "battle_timeout": analysis_result.battle_timeout,
        }

        print("Analysis result:", analysis_result)
        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing agent card: {str(e)}"
        )


class LauncherCheckRequest(BaseModel):
    launcher_url: str = Field(..., description="The launcher URL to check")


@router.post("/agents/check_launcher")
async def check_launcher_status(request: LauncherCheckRequest):
    """Check if a launcher URL is accessible and running."""
    try:
        import httpx
        
        launcher_url = request.launcher_url.rstrip('/')
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{launcher_url}/status")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    is_online = data.get("status") == "server up, with agent running"
                except:
                    is_online = False
            else:
                is_online = False
                
        return {
            "online": is_online,
            "status_code": response.status_code,
            "launcher_url": launcher_url
        }
        
    except Exception as e:
        print(f"Error checking launcher status: {str(e)}")
        return {
            "online": False,
            "error": str(e),
            "launcher_url": request.launcher_url
        }
