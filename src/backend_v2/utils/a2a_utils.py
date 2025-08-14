# -*- coding: utf-8 -*-
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional

from agentbeats.utils.agents import send_message_to_agent


async def reset_agent_trigger(
    self, launcher_url: str, agent_id: str, backend_url: str, extra_args: dict = None
) -> bool:
    """Reset an agent via its launcher."""
    httpx_client = None
    try:
        extra_args = extra_args or {}
        httpx_client = httpx.AsyncClient()

        reset_payload = {
            "signal": "reset",
            "agent_id": agent_id,
            "backend_url": backend_url,
            "extra_args": extra_args,
        }

        response = await httpx_client.post(f"{launcher_url}/reset", json=reset_payload)

        if response.status_code != 200:
            print(
                f"[a2a_utils] ERROR: Failed to reset agent at {launcher_url}: {response.status_code}"
            )
            return False
        else:
            print(f"[a2a_utils] INFO: Agent reset successfully at {launcher_url}")

        return True
    except Exception as e:
        print(f"[a2a_utils] ERROR: Error resetting agent at {launcher_url}: {str(e)}")
        return False
    finally:
        if httpx_client:
            await httpx_client.aclose()


async def notify_green_agent(
    self,
    endpoint: str,
    opponent_infos: List[Dict[str, Any]],
    battle_id: str,
    backend_url: str = "http://localhost:9000",
    green_agent_name: str = "green_agent",
    red_agent_names: Dict[str, str] = None,
) -> bool:
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
                    battle_id=battle_id, backend_url=backend_url, agent_name=agent_name
                )

        # kickoff signal
        battle_info = {
            "type": "battle_start",
            "battle_id": battle_id,
            "green_battle_context": {
                "battle_id": green_context.battle_id,
                "backend_url": green_context.backend_url,
                "agent_name": green_context.agent_name,
            },
            "red_battle_contexts": {
                url: {
                    "battle_id": ctx.battle_id,
                    "backend_url": ctx.backend_url,
                    "agent_name": ctx.agent_name,
                }
                for url, ctx in red_contexts.items()
            },
            "opponent_infos": opponent_infos,  # Keep for backward compatibility
        }

        # Use SDK function to send message
        print(f"[a2a_utils] INFO: About to send message to {endpoint}")
        try:
            response = await send_message_to_agent(endpoint, json.dumps(battle_info))
            print(f"[a2a_utils] INFO: Message sent successfully, response: {response}")
        except Exception as send_error:
            print(
                f"[a2a_utils] ERROR: Failed to send message to {endpoint}: {send_error}"
            )
            print(f"[a2a_utils] ERROR: Exception type: {type(send_error).__name__}")
            raise send_error

        # Return True if we got any response (not an error)
        success = response and not response.startswith("Error:")
        print(
            f"[a2a_utils] INFO: Green agent notification {'succeeded' if success else 'failed'}"
        )
        return success

    except Exception as e:
        print(
            f"[a2a_utils] ERROR: Error in notify_green_agent for {endpoint}: {str(e)}"
        )
        print(f"[a2a_utils] ERROR: Exception type: {type(e).__name__}")
        return False


async def send_battle_info(
    self,
    endpoint: str,
    battle_id: str,
    agent_name: str,
    agent_id: str,
    backend_url: str = "http://localhost:9000",
):
    try:
        battle_info = {
            "type": "battle_info",
            "battle_id": battle_id,
            "agent_name": agent_name,
            "agent_id": agent_id,
            "backend_url": backend_url,
        }

        # Use SDK function to send message
        print(f"[a2a_utils] INFO: About to send message to {endpoint}")
        try:
            response = await send_message_to_agent(endpoint, json.dumps(battle_info))
            print(f"[a2a_utils] INFO: Message sent successfully, response: {response}")
        except Exception as send_error:
            print(
                f"[a2a_utils] ERROR: Failed to send message to {endpoint}: {send_error}"
            )
            print(f"[a2a_utils] ERROR: Exception type: {type(send_error).__name__}")
            raise send_error

        # Return True if we got any response (not an error)
        success = response and not response.startswith("Error:")
        print(
            f"[a2a_utils] INFO: Green agent notification {'succeeded' if success else 'failed'}"
        )
        return success

    except Exception as e:
        print(
            f"[a2a_utils] ERROR: Error in notify_green_agent for {endpoint}: {str(e)}"
        )
        print(f"[a2a_utils] ERROR: Exception type: {type(e).__name__}")
        return False
