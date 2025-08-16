import httpx
import logging
import uuid
import time
import json
import asyncio
from typing import Dict, Any, Optional, List
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Part,
    Message,
    Role,
    TextPart,
)

from agentbeats.utils.agents import get_agent_card, send_message_to_agent

logger = logging.getLogger(__name__)

class AgentBeatsA2AClient:
    """Client for communicating with agents/launcher via A2A protocol using the official SDK."""
    
    def __init__(self):
        pass  # No longer need client caching since SDK handles it
            
    async def close(self):
        pass  # SDK handles cleanup
    
    async def get_agent_card(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get agent card using SDK function."""
        return await get_agent_card(endpoint)
            
    async def reset_agent_trigger(self, launcher_url: str, 
                                        agent_id: str, 
                                        backend_url: str, 
                                        extra_args: dict = None) -> bool:
        """Reset an agent via its launcher."""
        httpx_client = None
        try:
            extra_args = extra_args or {}
            httpx_client = httpx.AsyncClient()
            
            reset_payload = {
                "signal": "reset",
                "agent_id": agent_id,
                "backend_url": backend_url,
                "extra_args": extra_args
            }

            response = await httpx_client.post(
                f"{launcher_url}/reset",
                json=reset_payload
            )

            if response.status_code != 200:
                logger.error(f"Failed to reset agent at {launcher_url}: {response.status_code}")
                return False
            else:
                logger.info(f"Agent reset successfully at {launcher_url}")     
            
            return True
        except Exception as e:
            logger.error(f"Error resetting agent at {launcher_url}: {str(e)}")
            return False
        finally:
            if httpx_client:
                await httpx_client.aclose()
        
    async def notify_green_agent(self, 
                                endpoint: str,                                 
                                opponent_infos: List[Dict[str, Any]],
                                battle_id: str,
                                backend_url: str = "http://localhost:9000",
                                green_agent_name: str = "green_agent",
                                red_agent_names: Dict[str, str] = None,
                                task_config: str = "") -> bool:
        """Notify the green agent about a battle using SDK message sending."""
        try:
            # TODO: make this more eligant, for exmaple, 
            # the launcher should send PUT request after agent is really set
            await asyncio.sleep(5)
            
            # Import BattleContext here to avoid circular imports
            from agentbeats.logging import BattleContext
                
            # Create battle information with BattleContext objects (convert to dicts for JSON serialization)
            green_context = BattleContext(
                battle_id=battle_id, 
                backend_url=backend_url, 
                agent_name=green_agent_name,  # Use actual agent name from database
                task_config=task_config
            )
            
            red_contexts = {}
            for opp in opponent_infos:
                if opp.get("agent_url"):
                    # Use actual agent name from database if available, otherwise fall back to opponent info
                    agent_name = "red_agent"
                    if red_agent_names and opp["agent_url"] in red_agent_names:
                        agent_name = red_agent_names[opp["agent_url"]]
                    elif opp.get("name"):
                        agent_name = opp["name"]
                    
                    red_contexts[opp["agent_url"]] = BattleContext(
                        battle_id=battle_id, 
                        backend_url=backend_url, 
                        agent_name=agent_name
                    )
            
            # kickoff signal
            battle_info = {
                "type": "battle_start",
                "battle_id": battle_id,
                "green_battle_context": {
                    "battle_id": green_context.battle_id,
                    "backend_url": green_context.backend_url,
                    "agent_name": green_context.agent_name,
                    "task_config": f"Task description: {green_context.task_config}",
                },
                "red_battle_contexts": {
                    url: {
                        "battle_id": ctx.battle_id,
                        "backend_url": ctx.backend_url,
                        "agent_name": ctx.agent_name
                    }
                    for url, ctx in red_contexts.items()
                },
                "opponent_infos": opponent_infos,  # Keep for backward compatibility
            }
            
            # Debug: Test JSON serialization
            try:
                json_str = json.dumps(battle_info, indent=2)
                logger.info(f"JSON serialization successful, length: {len(json_str)}")
                logger.info(f"Sending battle info to {endpoint}: {json_str}")
            except Exception as json_error:
                logger.error(f"JSON serialization failed: {json_error}")
                logger.error(f"BattleContext objects may not be JSON serializable")
                # Try to serialize without BattleContext objects to isolate the issue
                try:
                    test_info = {
                        "type": "battle_start",
                        "battle_id": battle_id,
                        "opponent_infos": opponent_infos,
                        "task_config": task_config,
                    }
                    json.dumps(test_info)
                    logger.error("Basic info serializes fine, BattleContext is the issue")
                except Exception as e2:
                    logger.error(f"Even basic info fails: {e2}")
                raise json_error
            
            # Use SDK function to send message
            logger.info(f"About to send message to {endpoint}")
            try:
                response = await send_message_to_agent(endpoint, json.dumps(battle_info))
                logger.info(f"Message sent successfully, response: {response}")
            except Exception as send_error:
                logger.error(f"Failed to send message to {endpoint}: {send_error}")
                logger.error(f"Exception type: {type(send_error).__name__}")
                raise send_error
            
            # Return True if we got any response (not an error)
            success = response and not response.startswith("Error:")
            logger.info(f"Green agent notification {'succeeded' if success else 'failed'}")
            return success
                            
        except Exception as e:
            logger.error(f"Error in notify_green_agent for {endpoint}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return False

    async def send_battle_info(self, 
                                endpoint: str,                                 
                                battle_id: str,
                                agent_name: str,
                                agent_id: str,
                                backend_url: str = "http://localhost:9000"):
        try:
            battle_info = {
                "type": "battle_info",
                "battle_id": battle_id,
                "agent_name": agent_name,
                "agent_id": agent_id,
                "backend_url": backend_url,
            }
            
            # Use SDK function to send message
            logger.info(f"About to send message to {endpoint}")
            try:
                response = await send_message_to_agent(endpoint, json.dumps(battle_info))
                logger.info(f"Message sent successfully, response: {response}")
            except Exception as send_error:
                logger.error(f"Failed to send message to {endpoint}: {send_error}")
                logger.error(f"Exception type: {type(send_error).__name__}")
                raise send_error
            
            # Return True if we got any response (not an error)
            success = response and not response.startswith("Error:")
            logger.info(f"Green agent notification {'succeeded' if success else 'failed'}")
            return success
                            
        except Exception as e:
            logger.error(f"Error in notify_green_agent for {endpoint}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return False

# Create a client instance
a2a_client = AgentBeatsA2AClient()
