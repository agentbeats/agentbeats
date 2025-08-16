import asyncio
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Literal
from agents import Agent, Runner
import httpx

from ..db.storage import db
from ..a2a_client import a2a_client
from ..auth.middleware import get_current_user, get_optional_user
from ..services.match_storage import MatchStorage
from ..services.role_matcher import RoleMatcher

# =============================================================================
# AGENT REGISTRATION LOGGING CONFIGURATION
# =============================================================================
# Configure dedicated logger for agent registration operations
agent_registration_logger = logging.getLogger("agent_registration")
agent_registration_logger.setLevel(logging.ERROR)  # Only log errors

# Create console handler if it doesn't exist
if not agent_registration_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "%(asctime)s - [AGENT_REG] - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    agent_registration_logger.addHandler(console_handler)
    agent_registration_logger.propagate = False  # Prevent duplicate logs

router = APIRouter()

# Initialize services
match_storage = MatchStorage()
role_matcher = RoleMatcher()


async def analyze_agent_matches_async(
    agent_id: str, current_user: Dict[str, Any]
):
    """Asynchronously analyze and store role matches for a newly registered agent."""
    try:
        # Get the agent
        agent = db.read("agents", agent_id)
        if not agent:
            return

        is_green = agent["register_info"]["is_green"]
        agent_alias = agent["register_info"]["alias"]

        if is_green:
            # Green agent: analyze against all non-green agents
            other_agents = [
                a
                for a in db.list("agents")
                if not a["register_info"]["is_green"]
                and a["agent_id"] != agent_id
            ]
        else:
            # Non-green agent: analyze against all green agents
            other_agents = [
                a
                for a in db.list("agents")
                if a["register_info"]["is_green"] and a["agent_id"] != agent_id
            ]

        matches_created = []

        for j, other_agent in enumerate(other_agents):
            other_alias = other_agent["register_info"]["alias"]

            # Validate agent cards exist
            if not agent.get("agent_card") or not other_agent.get(
                "agent_card"
            ):
                continue

            try:
                if is_green:
                    # Green agent's requirements vs other agent
                    requirements = agent["register_info"].get(
                        "participant_requirements", []
                    )

                    result = await role_matcher.analyze_agent_for_roles(
                        agent["agent_card"],
                        requirements,
                        other_agent["agent_card"],
                    )

                    if result.get("matched_roles"):
                        match_record = {
                            "green_agent_id": agent_id,
                            "other_agent_id": other_agent["agent_id"],
                            "matched_roles": result["matched_roles"],
                            "reasons": result["reasons"],
                            "confidence_score": result.get(
                                "confidence_score", 0.0
                            ),
                            "created_by": current_user["id"],
                        }

                        created_match = match_storage.create_match(
                            match_record
                        )
                        matches_created.append(created_match)
                else:
                    # Other agent vs green agent's requirements
                    requirements = other_agent["register_info"].get(
                        "participant_requirements", []
                    )
                    result = await role_matcher.analyze_agent_for_roles(
                        other_agent["agent_card"],
                        requirements,
                        agent["agent_card"],
                    )

                    if result.get("matched_roles"):
                        match_record = {
                            "green_agent_id": other_agent["agent_id"],
                            "other_agent_id": agent_id,
                            "matched_roles": result["matched_roles"],
                            "reasons": result["reasons"],
                            "confidence_score": result.get(
                                "confidence_score", 0.0
                            ),
                            "created_by": current_user["id"],
                        }

                        created_match = match_storage.create_match(
                            match_record
                        )
                        matches_created.append(created_match)

            except Exception as e:
                agent_registration_logger.error(
                    f"Error analyzing {agent_alias} vs {other_alias}: {str(e)}"
                )
                continue

    except Exception as e:
        agent_registration_logger.error(
            f"Error analyzing matches for agent {agent_id}: {e}"
        )
        import traceback

        traceback.print_exc()


EXTRACT_SUFFIX_PROMPT = """
You are an expert system for extracting relevant parts of task descriptions.
Given a task description, extract the directory path or key phrase that identifies the task.
For example, from "The target task directory is hackthebox/cyber-apocalypse-2024/reversing/[Very Easy] PackedAway," extract "hackthebox/cyber-apocalypse-2024/reversing/[Very Easy] PackedAway."
From "Task index = 1" or "task_index = 1", etc. just extract "1". (Don't include "Task index" in the output.)
From "Random 5", extract "Random 5".
"""


async def extract_suffix_from_task_config(
    task_config: str,
) -> Dict[str, str]:
    """Extract suffix from task description using LLM."""
    if not task_config:
        raise HTTPException(status_code=400, detail="Missing task description")

    agent_registration_logger.info(
        f"Extracting suffix from task description: {task_config}"
    )
    extract_suffix_agent = Agent(
        name="Task Description Suffix Extractor",
        instructions=EXTRACT_SUFFIX_PROMPT,
        output_type=str,
        model="gpt-4o",
    )

    response = await Runner.run(
        extract_suffix_agent,
        input=task_config,
    )

    suffix = response.final_output_as(str)
    agent_registration_logger.info(f"Extracted suffix: {suffix}")
    return suffix


@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def register_agent(
    agent_info: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Register a new agent."""
    agent_registration_logger.info(f"🚀 Agent registration request received")
    agent_registration_logger.info(
        f"📋 Registration info: alias={agent_info.get('alias', 'N/A')}, is_green={agent_info.get('is_green', 'N/A')}"
    )

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
                status_code=400,
                detail="Missing required fields: alias, agent_url, launcher_url, is_green, roles",
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
        if (
            agent_info["is_green"]
            and "participant_requirements" not in agent_info
        ):
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
                status_code=400,
                detail="Failed to get agent card from agent_url",
            )

        # Use agent card name as alias if no alias provided
        if not agent_info.get("alias") or agent_info["alias"].strip() == "":
            agent_info["alias"] = agent_card.get("name", "Unnamed Agent")

        # Use LLM to extract suffix from task description
        if agent_info.get("task_config"):
            agent_registration_logger.info(
                f"Task description provided: {agent_info['task_config']}"
            )
            agent_suffix = await extract_suffix_from_task_config(
                agent_info["task_config"]
            )
            agent_info["alias"] += f" ({agent_suffix})"

        # Create agent record
        elo_rating = None if agent_info.get("is_green") else 1000
        agent_record = {
            "register_info": agent_info,
            "agent_card": agent_card,
            "status": "unlocked",
            "ready": False,
            "user_id": current_user["id"],  # Add user ownership
            "created_by": current_user.get("user_metadata", {}).get(
                "name", current_user.get("email", "unknown")
            ),  # Use display name or email
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
                    "error_rate": 0.0,
                },
            },
        }

        # Save to database
        agent_registration_logger.info(f"💾 Saving agent to database...")
        created_agent = db.create("agents", agent_record)
        agent_registration_logger.info(
            f"✅ Agent saved with ID: {created_agent['agent_id']}"
        )

        # Trigger role matching analysis asynchronously
        agent_registration_logger.info(
            f"🔄 Triggering role matching analysis..."
        )
        try:
            asyncio.create_task(
                analyze_agent_matches_async(
                    created_agent["agent_id"], current_user
                )
            )
            agent_registration_logger.info(
                f"✅ Role analysis task created successfully"
            )
        except Exception as e:
            # Log error but don't fail registration
            agent_registration_logger.warning(
                f"⚠️ Failed to trigger role analysis: {e}"
            )

        return created_agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error registering agent: {str(e)}"
        )


async def check_agents_liveness(
    agents: List[Dict[str, Any]], max_concurrent: int = 10
) -> List[Dict[str, Any]]:
    """Check liveness for a list of agents and add 'live' field to each agent."""

    async def check_agent_liveness(agent):
        """Check liveness for a single agent."""
        agent_url = agent.get("register_info", {}).get("agent_url")
        launcher_url = agent.get("register_info", {}).get("launcher_url")

        async def check_agent_card():
            """Check if agent URL is accessible and can return agent card."""
            if not agent_url:
                return False
            try:
                # Use asyncio.wait_for to add additional timeout layer
                agent_card = await asyncio.wait_for(
                    a2a_client.get_agent_card(agent_url), timeout=1.5
                )
                return bool(agent_card)
            except (asyncio.TimeoutError, Exception):
                return False

        async def check_launcher():
            """Check if launcher is alive."""
            if not launcher_url:
                return False
            try:
                # Use asyncio.wait_for to add additional timeout layer
                launcher_status = await asyncio.wait_for(
                    check_launcher_status({"launcher_url": launcher_url}),
                    timeout=1.5,
                )
                return launcher_status.get("online", False)
            except (asyncio.TimeoutError, Exception):
                return False

        # Run both checks concurrently for this agent
        try:
            agent_card_accessible, launcher_alive = await asyncio.gather(
                check_agent_card(), check_launcher(), return_exceptions=False
            )
            agent["live"] = agent_card_accessible and launcher_alive
        except Exception:
            agent["live"] = False
        return agent

    # Use semaphore to limit concurrent checks
    semaphore = asyncio.Semaphore(max_concurrent)

    async def check_with_semaphore(agent):
        async with semaphore:
            return await check_agent_liveness(agent)

    # Run all liveness checks with concurrency limit
    checked_agents = await asyncio.gather(
        *[check_with_semaphore(agent) for agent in agents],
        return_exceptions=True,
    )

    # Handle any exceptions during liveness checks
    for i, result in enumerate(checked_agents):
        if isinstance(result, Exception):
            # If exception, mark agent as not live
            agents[i]["live"] = False
        else:
            agents[i] = result

    return agents


@router.get("/agents")
async def list_agents(
    check_liveness: bool = False,
    current_user: Dict[str, Any] = Depends(get_optional_user),
) -> List[Dict[str, Any]]:
    """List all agents with optional liveness check."""
    try:
        agents = db.list("agents")

        # Filter agents by ownership if user is authenticated
        if current_user:
            # Show user's own agents first, then public agents (no user_id)
            user_agents = [
                agent
                for agent in agents
                if agent.get("user_id") == current_user["id"]
            ]
            public_agents = [
                agent for agent in agents if not agent.get("user_id")
            ]
            dev_agents = [
                agent
                for agent in agents
                if agent.get("user_id") == "dev-user-id"
            ]
            agents = user_agents + public_agents + dev_agents
        else:
            # If not authenticated, only show public agents
            agents = [agent for agent in agents if not agent.get("user_id")]

        if check_liveness:
            agents = await check_agents_liveness(agents)

        return agents
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing agents: {str(e)}"
        )


@router.get("/agents/my")
async def get_my_agents(
    check_liveness: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get all agents owned by the current user with optional liveness check."""
    try:
        agents = db.list("agents")
        user_agents = [
            agent
            for agent in agents
            if agent.get("user_id") == current_user["id"]
        ]

        if check_liveness:
            user_agents = await check_agents_liveness(user_agents)

        return user_agents
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving user agents: {str(e)}"
        )


@router.get("/agents/{agent_id}")
def get_agent(
    agent_id: str, current_user: Dict[str, Any] = Depends(get_optional_user)
) -> Dict[str, Any]:
    """Get a single agent by ID."""
    try:
        agent = db.read("agents", agent_id)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent with ID {agent_id} not found"
            )

        # Allow all users to view all agents - no ownership restrictions for viewing
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving agent: {str(e)}"
        )


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete an agent (only by owner)."""
    try:
        agent = db.read("agents", agent_id)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent with ID {agent_id} not found"
            )

        # Check ownership - only the owner can delete their agent
        agent_user_id = agent.get("user_id")
        if agent_user_id and agent_user_id != current_user["id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied - can only delete your own agents",
            )

        # Delete associated role matches first
        try:
            deleted_matches = match_storage.delete_matches_for_agent(agent_id)
            if deleted_matches > 0:
                agent_registration_logger.info(
                    f"Deleted {deleted_matches} role matches for agent {agent_id}"
                )
        except Exception as e:
            agent_registration_logger.error(
                f"Error deleting role matches for agent {agent_id}: {str(e)}"
            )
            # Continue with agent deletion even if match cleanup fails

        # Delete the agent
        db.delete("agents", agent_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting agent: {str(e)}"
        )


@router.put("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_agent(
    agent_id: str,
    update: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_optional_user),
):
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

        # For 'ready' status updates (from agent launcher), allow without authentication
        if "ready" in update and len(update) == 1:
            agent["ready"] = bool(update["ready"])
            db.update("agents", agent_id, agent)
            return None

        # For other updates, require authentication and ownership check
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required for agent updates",
            )

        # Check ownership - only the owner can update their agent
        agent_user_id = agent.get("user_id")
        if agent_user_id and agent_user_id != current_user["id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied - can only update your own agents",
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
        raise HTTPException(
            status_code=500, detail=f"Error updating agent: {str(e)}"
        )


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
            raise HTTPException(
                status_code=400, detail="agent_url cannot be empty"
            )

        # Get agent card from the agent_url using a2a_client
        agent_card = await a2a_client.get_agent_card(agent_url)
        if not agent_card:
            raise HTTPException(
                status_code=400,
                detail="Failed to get agent card from agent_url",
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
            raise HTTPException(
                status_code=400, detail="agent_card cannot be empty"
            )

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


@router.post("/agents/check_launcher")
async def check_launcher_status(request: Dict[str, Any]):
    """Check if a launcher URL is accessible and running."""
    try:
        if "launcher_url" not in request:
            raise HTTPException(
                status_code=400, detail="Missing required field: launcher_url"
            )

        launcher_url = request["launcher_url"]
        if not launcher_url:
            raise HTTPException(
                status_code=400, detail="launcher_url cannot be empty"
            )

        launcher_url_clean = launcher_url.rstrip("/")

        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(f"{launcher_url_clean}/status")

            if response.status_code == 200:
                try:
                    data = response.json()
                    is_online = (
                        data.get("status") == "server up, with agent running"
                    )
                except:
                    is_online = False
            else:
                is_online = False

        return {
            "online": is_online,
            "status_code": response.status_code,
            "launcher_url": launcher_url_clean,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking launcher status: {str(e)}")
        return {
            "online": False,
            "error": str(e),
            "launcher_url": request.get("launcher_url", ""),
        }
