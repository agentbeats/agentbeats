import asyncio
import httpx
from fastapi import HTTPException
from typing import Dict, Any, List
from agentbeats.utils.agents import get_agent_card


from ..db import agent_repo, instance_repo


async def check_agents_liveness(agents: List[Dict[str, Any]], max_concurrent: int = 10) -> List[Dict[str, Any]]:
    """Check liveness for a list of agents and add 'live' field to each agent."""
    async def check_agent_liveness(agent):
        """Check liveness for a single agent."""
        if agent.get("is_hosted"):
            agent["live"] = True  # Hosted agents are always considered live
            return agent

        # Else is remote agent, get tne instance and then get URLs
        agent_id = agent.get("id")
        instance = instance_repo.get_agent_instances_by_agent_id(agent_id)[0]
        agent_url = instance.get("agent_url")
        launcher_url = instance.get("launcher_url")
        
        async def check_agent_card():
            """Check if agent URL is accessible and can return agent card."""
            if not agent_url:
                return False
            try:
                # Use asyncio.wait_for to add additional timeout layer
                agent_card = await asyncio.wait_for(
                    get_agent_card(agent_url), 
                    timeout=1.5
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
                    timeout=1.5
                )
                return launcher_status.get("online", False)
            except (asyncio.TimeoutError, Exception):
                return False
        
        # Run both checks concurrently for this agent
        try:
            agent_card_accessible, launcher_alive = await asyncio.gather(
                check_agent_card(),
                check_launcher(),
                return_exceptions=False
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
        return_exceptions=True
    )
    
    # Handle any exceptions during liveness checks
    for i, result in enumerate(checked_agents):
        if isinstance(result, Exception):
            # If exception, mark agent as not live
            agents[i]["live"] = False
        else:
            agents[i] = result
    
    return agents

async def check_launcher_status(launcher_url: str) -> Dict[str, Any]:
    """Check if a launcher URL is accessible and running."""
    try:
            
        launcher_url_clean = launcher_url.rstrip('/')
        
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(f"{launcher_url_clean}/status")
            
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
            "launcher_url": launcher_url_clean
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking launcher status: {str(e)}")
        return {
            "online": False,
            "error": str(e),
            "launcher_url": launcher_url
        }