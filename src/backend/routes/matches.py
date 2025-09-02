from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
from ..db.storage import db
from ..auth.middleware import get_current_user
from ..services.match_storage import MatchStorage
from ..services.role_matcher import RoleMatcher
import asyncio

# =============================================================================
# MATCHES API LOGGING CONFIGURATION
# =============================================================================
# Configure dedicated logger for matches API operations
matches_api_logger = logging.getLogger('matches_api')
matches_api_logger.setLevel(logging.ERROR)  # Only log errors

# Create console handler if it doesn't exist
if not matches_api_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - [MATCHES_API] - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    matches_api_logger.addHandler(console_handler)
    matches_api_logger.propagate = False  # Prevent duplicate logs

router = APIRouter()
match_storage = MatchStorage()
role_matcher = RoleMatcher()

@router.get("/matches/green-agent/{green_agent_id}")
async def get_matches_for_green_agent(
    green_agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get all role matches for a specific green agent.
    
    Note: All authenticated users can view matches for any agent.
    This enables battle creation by allowing users to see compatible agents.
    """
    try:
        # Verify green agent exists
        green_agent = db.read("agents", green_agent_id)
        if not green_agent:
            raise HTTPException(status_code=404, detail="Green agent not found")
        
        # REMOVED: Ownership check - all authenticated users can view matches
        # This enables cross-user battle creation by showing compatible agents
        
        # Get all matches for this green agent
        matches = match_storage.get_matches_for_green_agent(green_agent_id)
        
        # Enrich with agent information
        enriched_matches = []
        for match in matches:
            other_agent = db.read("agents", match["other_agent_id"])
            if other_agent:
                enriched_match = {
                    **match,
                    "other_agent": {
                        "agent_id": other_agent["agent_id"],
                        "alias": other_agent["register_info"]["alias"],
                        "name": other_agent["agent_card"].get("name"),
                        "description": other_agent["agent_card"].get("description")
                    }
                }
                enriched_matches.append(enriched_match)
        
        return enriched_matches
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/agent/{agent_id}")
async def get_matches_for_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all matches where an agent appears (either as green or other).
    
    Note: All authenticated users can view matches for any agent.
    This enables battle creation by allowing users to see compatible agents.
    """
    try:
        # Verify agent exists
        agent = db.read("agents", agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # REMOVED: Ownership check - all authenticated users can view matches
        # This enables cross-user battle creation by showing compatible agents
        
        return match_storage.get_matches_for_agent(agent_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/role/{role_name}")
async def get_matches_by_role(
    role_name: str,
    min_confidence: float = 0.0,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get all matches for a specific role.
    
    Note: This endpoint is already public for all authenticated users.
    It shows role-based compatibility across all agents.
    """
    try:
        matches = match_storage.get_matches_by_role(role_name, min_confidence)
        
        # Enrich with agent information
        enriched_matches = []
        for match in matches:
            green_agent = db.read("agents", match["green_agent_id"])
            other_agent = db.read("agents", match["other_agent_id"])
            
            if green_agent and other_agent:
                enriched_match = {
                    **match,
                    "green_agent": {
                        "agent_id": green_agent["agent_id"],
                        "alias": green_agent["register_info"]["alias"],
                        "name": green_agent["agent_card"].get("name")
                    },
                    "other_agent": {
                        "agent_id": other_agent["agent_id"],
                        "alias": other_agent["register_info"]["alias"],
                        "name": other_agent["agent_card"].get("name")
                    }
                }
                enriched_matches.append(enriched_match)
        
        return enriched_matches
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/matches/analyze/{agent_id}")
async def analyze_agent_matches(
    agent_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze and store role matches for a specific agent."""
    try:
        # Get the agent
        agent = db.read("agents", agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check ownership
        if agent.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        is_green = agent["register_info"]["is_green"]
        
        if is_green:
            # Green agent: analyze against all non-green agents
            other_agents = [
                a for a in db.list("agents") 
                if not a["register_info"]["is_green"] and a["agent_id"] != agent_id
            ]
        else:
            # Non-green agent: analyze against all green agents
            other_agents = [
                a for a in db.list("agents") 
                if a["register_info"]["is_green"] and a["agent_id"] != agent_id
            ]
        
        matches_created = []
        
        for other_agent in other_agents:
            if is_green:
                # Green agent's requirements vs other agent
                requirements = agent["register_info"].get("participant_requirements", [])
                result = await role_matcher.analyze_agent_for_roles(
                    agent["agent_card"],
                    requirements,
                    other_agent["agent_card"]
                )
                
                if result.get("matched_roles"):
                    match_record = {
                        "green_agent_id": agent_id,
                        "other_agent_id": other_agent["agent_id"],
                        "matched_roles": result["matched_roles"],
                        "reasons": result["reasons"],
                        "confidence_score": result.get("confidence_score", 0.0),
                        "created_by": current_user["id"]
                    }
                    
                    created_match = match_storage.create_match(match_record)
                    matches_created.append(created_match)
            else:
                # Other agent vs green agent's requirements
                requirements = other_agent["register_info"].get("participant_requirements", [])
                result = await role_matcher.analyze_agent_for_roles(
                    other_agent["agent_card"],
                    requirements,
                    agent["agent_card"]
                )
                
                if result.get("matched_roles"):
                    match_record = {
                        "green_agent_id": other_agent["agent_id"],
                        "other_agent_id": agent_id,
                        "matched_roles": result["matched_roles"],
                        "reasons": result["reasons"],
                        "confidence_score": result.get("confidence_score", 0.0),
                        "created_by": current_user["id"]
                    }
                    
                    created_match = match_storage.create_match(match_record)
                    matches_created.append(created_match)
        
        return {
            "message": f"Analyzed {len(matches_created)} matches",
            "matches_created": len(matches_created)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/matches/{match_id}")
async def delete_match(
    match_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific match."""
    try:
        # For now, allow deletion of any match
        # In the future, you might want to check ownership
        success = match_storage.delete_match(match_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Match not found")
        
        return {"message": "Match deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/matches/agent/{agent_id}")
async def delete_matches_for_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete all matches involving a specific agent.
    
    Note: This operation requires ownership of the agent.
    Only the agent owner can delete their matches.
    """
    try:
        # Verify agent exists and user has access
        agent = db.read("agents", agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        deleted_count = match_storage.delete_matches_for_agent(agent_id)
        
        return {
            "message": f"Deleted {deleted_count} matches",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/stats")
async def get_match_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get statistics about stored matches."""
    try:
        stats = match_storage.get_match_stats()
        return stats
        
    except Exception as e:
        matches_api_logger.error(f"Error getting match stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/matches/clear-cache")
async def clear_matcher_cache(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear the in-memory cache of the role matcher."""
    try:
        role_matcher.clear_cache()
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 