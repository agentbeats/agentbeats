# -*- coding: utf-8 -*-

"""
Battle Processor for AgentBeats Backend V2.

Handles the actual battle execution logic, adapted from backend v1.
"""

import asyncio
import logging
import threading
import time
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..db import agent_repo, battle_repo
from ..utils import a2a_utils


logger = logging.getLogger("battle_processor")

# TODO: configurable from frontend constants / database
# Configuration constants
DEFAULT_READY_TIMEOUT = 120
DEFAULT_BATTLE_TIMEOUT = 300


async def process_battle(battle_id: str, battle_data: Dict[str, Any]) -> bool:
    """
    Main battle processor function - handles the entire battle lifecycle.
    
    This is the core battle execution logic that:
    1. Validates and locks agents
    2. Resets agent states
    3. Waits for agents to be ready
    4. Executes the battle
    5. Handles timeouts and cleanup
    
    Args:
        battle_id: Unique battle identifier
        battle_data: Battle configuration containing green_agent_id, participants, config, etc.
        
    Returns:
        True if battle completed successfully, False if there were errors
    """
    try:
        logger.info(f"Starting battle processor for {battle_id}")
        
        # Get battle from database
        battle = battle_repo.get_battle(battle_id)
        if not battle:
            logger.error(f"Battle {battle_id} not found in database")
            return False
            
        # Update battle state to running
        battle['state'] = 'running'
        battle_repo.update_battle(battle_id, {'state': 'running'})
        
        # Extract battle configuration
        green_agent_id = battle_data.get('green_agent_id') or battle.get('green_agent_id')
        
        # Get participants - must be provided in correct format
        participants = battle_data.get('participants') or battle.get('participants', [])
        if not participants:
            error_msg = "No participants provided in battle data"
            logger.error(f"Battle {battle_id}: {error_msg}")
            await _finish_battle_with_error(battle_id, error_msg)
            return False
        
        config = battle_data.get('config', {})
        
        logger.info(f"Battle {battle_id}: green_agent={green_agent_id}, participants={participants}")
        
        # Step 1: Agent validation
        green_agent, opponent_agents = await _validate_battle_agents(battle_id, green_agent_id, participants)
        if not green_agent or not opponent_agents:
            return False
            
        # Step 2: Lock agents
        all_agent_ids = [green_agent_id] + [_extract_agent_id(op) for op in participants]
        await _lock_battle_agents(battle_id, all_agent_ids)
        
        # Step 3: Reset agents
        opponent_info_for_green = await _reset_battle_agents(battle_id, green_agent, opponent_agents, participants)
        if opponent_info_for_green is None:
            await _unlock_battle_agents(battle_id, all_agent_ids)
            return False
            
        # Step 4: Wait for agents to be ready
        ready_success = await _wait_for_agents_ready(battle_id, all_agent_ids)
        if not ready_success:
            await _unlock_battle_agents(battle_id, all_agent_ids)
            return False
            
        # Step 5: Send battle info to all agents
        battle_info_success = await _send_battle_info_to_agents(battle_id, green_agent, opponent_info_for_green, participants, all_agent_ids)
        if not battle_info_success:
            await _unlock_battle_agents(battle_id, all_agent_ids)
            return False
            
        # Step 6: Setup battle timeout and start battle
        battle_timeout = green_agent.get('register_info', {}).get('battle_timeout', DEFAULT_BATTLE_TIMEOUT)
        _start_battle_timeout(battle_id, battle_timeout)
        
        # Step 7: Notify green agent to start battle
        notify_success = await _notify_green_agent_start_battle(battle_id, green_agent, opponent_info_for_green)
        if not notify_success:
            await _unlock_battle_agents(battle_id, all_agent_ids)
            return False
            
        logger.info(f"Battle {battle_id}: Battle started successfully")
        return True
        
    except Exception as e:
        logger.error(f"Battle {battle_id}: Exception during processing: {str(e)}")
        await _finish_battle_with_error(battle_id, f"Processing error: {str(e)}")
        return False


async def _finish_battle_with_error(battle_id: str, error_message: str) -> None:
    """
    Finish a battle with an error state.
    
    Args:
        battle_id: Battle identifier
        error_message: Error description
    """
    try:
        error_data = {
            'state': 'error',
            'error': error_message,
            'finished_at': datetime.utcnow().isoformat() + 'Z'
        }
        battle_repo.update_battle(battle_id, error_data)
        logger.info(f"Battle {battle_id}: Marked as error - {error_message}")
    except Exception as e:
        logger.error(f"Failed to update battle {battle_id} with error state: {str(e)}")


def _extract_agent_id(opponent_info: Any) -> str:
    """Extract agent ID from opponent info (dict or string)."""
    if isinstance(opponent_info, dict):
        return opponent_info.get('agent_id')
    return opponent_info


async def _validate_battle_agents(battle_id: str, green_agent_id: str, participants: List[Any]) -> tuple:
    """
    Validate all battle agents exist and are accessible.
    
    Returns:
        tuple: (green_agent, opponent_agents) or (None, None) if validation fails
    """
    # Validate green agent
    green_agent = agent_repo.get_agent(green_agent_id)
    if not green_agent:
        error_msg = "Green agent not found"
        logger.error(f"Battle {battle_id}: {error_msg}")
        await _finish_battle_with_error(battle_id, error_msg)
        return None, None
        
    # Validate participant agents
    opponent_agents = []
    for participant_info in participants:
        participant_id = _extract_agent_id(participant_info)
        participant_agent = agent_repo.get_agent(participant_id)
        if not participant_agent:
            error_msg = f"Participant agent {participant_id} not found"
            logger.error(f"Battle {battle_id}: {error_msg}")
            await _finish_battle_with_error(battle_id, error_msg)
            return None, None
        opponent_agents.append(participant_agent)
        
    logger.info(f"Battle {battle_id}: All agents validated successfully")
    return green_agent, opponent_agents


async def _lock_battle_agents(battle_id: str, agent_ids: List[str]) -> None:
    """Lock all agents participating in the battle."""
    for agent_id in agent_ids:
        agent = agent_repo.get_agent(agent_id)
        if agent:
            agent["status"] = "locked"
            agent_repo.update_agent(agent_id, agent)
    logger.info(f"Battle {battle_id}: Agents locked")


async def _unlock_battle_agents(battle_id: str, agent_ids: List[str]) -> None:
    """Unlock all agents and set them to not ready."""
    for agent_id in agent_ids:
        agent = agent_repo.get_agent(agent_id)
        if agent:
            agent["status"] = "unlocked"
            agent["ready"] = False
            agent_repo.update_agent(agent_id, agent)
    logger.info(f"Battle {battle_id}: Agents unlocked")


async def _reset_battle_agents(battle_id: str, green_agent: Dict[str, Any], 
                              opponent_agents: List[Dict[str, Any]], 
                              participants: List[Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Reset all battle agents via their launchers.
    
    Returns:
        List of opponent info for green agent, or None if reset failed
    """
    backend_url = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:9000")
    
    # Reset green agent
    green_launcher = green_agent["register_info"]["launcher_url"]
    green_reset = await a2a_utils.reset_agent_trigger(
        green_launcher, 
        agent_id=green_agent["agent_id"], 
        backend_url=backend_url,
        extra_args={}
    )
    if not green_reset:
        error_msg = "Failed to reset green agent"
        logger.error(f"Battle {battle_id}: {error_msg}")
        await _finish_battle_with_error(battle_id, error_msg)
        return None
        
    # Reset opponent agents and prepare info for green agent
    opponent_info_for_green = []
    for idx, opponent_agent in enumerate(opponent_agents):
        opponent_launcher = opponent_agent["register_info"].get("launcher_url")
        opponent_reset = await a2a_utils.reset_agent_trigger(
            opponent_launcher,
            agent_id=opponent_agent["agent_id"],
            backend_url=backend_url,
            extra_args={}
        )
        if not opponent_reset:
            error_msg = f"Failed to reset opponent {opponent_agent['agent_id']}"
            logger.error(f"Battle {battle_id}: {error_msg}")
            await _finish_battle_with_error(battle_id, error_msg)
            return None
            
        # Prepare opponent info for green agent
        if idx < len(participants):
            original_name = participants[idx].get("name", "red_agent") if isinstance(participants[idx], dict) else "red_agent"
        else:
            original_name = "red_agent"
            
        agent_name = opponent_agent.get("register_info", {}).get("alias", original_name)
        agent_url = opponent_agent["register_info"].get("agent_url")
        
        opponent_info_for_green.append({
            "name": agent_name,
            "agent_url": agent_url
        })
        
    logger.info(f"Battle {battle_id}: All agents reset successfully")
    return opponent_info_for_green


async def _wait_for_agents_ready(battle_id: str, agent_ids: List[str]) -> bool:
    """
    Wait for all agents to be ready.
    
    Returns:
        True if all agents are ready within timeout, False otherwise
    """
    ready_timeout = DEFAULT_READY_TIMEOUT
    logger.info(f"Battle {battle_id}: Waiting for agents to be ready (timeout: {ready_timeout}s)")
    
    start_time = time.time()
    while time.time() - start_time < ready_timeout:
        all_ready = True
        for agent_id in agent_ids:
            agent = agent_repo.get_agent(agent_id)
            if not agent or not agent.get("ready", False):
                all_ready = False
                break
        if all_ready:
            logger.info(f"Battle {battle_id}: All agents ready")
            return True
        await asyncio.sleep(5)
        
    error_msg = f"Not all agents ready after {ready_timeout} seconds"
    logger.error(f"Battle {battle_id}: {error_msg}")
    await _finish_battle_with_error(battle_id, error_msg)
    return False


async def _send_battle_info_to_agents(battle_id: str, green_agent: Dict[str, Any],
                                    opponent_info_for_green: List[Dict[str, Any]],
                                    participants: List[Any], agent_ids: List[str]) -> bool:
    """
    Send battle info to all participating agents.
    
    Returns:
        True if all agents acknowledged battle info, False otherwise
    """
    backend_url = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:9000")
    green_agent_url = green_agent["register_info"]["agent_url"]
    
    if not green_agent_url:
        error_msg = "Green agent url not found"
        logger.error(f"Battle {battle_id}: {error_msg}")
        await _finish_battle_with_error(battle_id, error_msg)
        return False
        
    # Prepare agents info
    agents_info = {}
    agents_info["green_agent"] = {
        "agent_id": green_agent["agent_id"],
        "agent_url": green_agent_url,
        "agent_name": "green_agent"
    }
    
    for idx, op_info in enumerate(opponent_info_for_green):
        if idx < len(agent_ids) - 1:  # -1 because first is green agent
            op_id = agent_ids[idx + 1]
            op_name = participants[idx].get("name", "no_name") if isinstance(participants[idx], dict) else "red_agent"
            agents_info[op_info["name"]] = {
                "agent_id": op_id,
                "agent_url": op_info["agent_url"],
                "agent_name": op_name
            }
    
    # Send battle info to all agents
    for name, agent_info in agents_info.items():
        success = await a2a_utils.send_battle_info(
            endpoint=agent_info["agent_url"],
            battle_id=battle_id,
            agent_name=agent_info["agent_name"],
            agent_id=agent_info["agent_id"],
            backend_url=backend_url,
        )
        if not success:
            error_msg = f"Agent {name} failed to respond to battle info"
            logger.error(f"Battle {battle_id}: {error_msg}")
            await _finish_battle_with_error(battle_id, error_msg)
            return False
            
    logger.info(f"Battle {battle_id}: Battle info sent to all agents successfully")
    return True


def _start_battle_timeout(battle_id: str, timeout: int) -> None:
    """Start a background thread to handle battle timeout."""
    timeout_thread = threading.Thread(
        target=_check_battle_timeout,
        args=(battle_id, timeout),
        daemon=True
    )
    timeout_thread.start()
    logger.info(f"Battle {battle_id}: Battle timeout set to {timeout} seconds")


def _check_battle_timeout(battle_id: str, timeout: int) -> None:
    """Check if a battle has timed out (runs in background thread)."""
    time.sleep(timeout)
    
    battle = battle_repo.get_battle(battle_id)
    if battle and battle.get("state") == "running":
        logger.info(f"Battle {battle_id}: Battle timed out after {timeout} seconds")
        result_data = {
            "state": "finished",
            "result": {
                "winner": "draw",
                "detail": {"message": "Battle timed out"},
                "finish_time": datetime.utcnow().isoformat() + "Z"
            },
            "finished_at": datetime.utcnow().isoformat() + "Z"
        }
        battle_repo.update_battle(battle_id, result_data)
        
        # Unlock agents
        participant_ids = []
        if "participants" in battle:
            participant_ids = [_extract_agent_id(op) for op in battle["participants"]]
        all_agent_ids = [battle.get("green_agent_id")] + participant_ids
        
        for agent_id in all_agent_ids:
            if agent_id:
                agent = agent_repo.get_agent(agent_id)
                if agent:
                    agent["status"] = "unlocked"
                    agent["ready"] = False
                    agent_repo.update_agent(agent_id, agent)


async def _notify_green_agent_start_battle(battle_id: str, green_agent: Dict[str, Any],
                                          opponent_info_for_green: List[Dict[str, Any]]) -> bool:
    """
    Notify the green agent to start the battle.
    
    Returns:
        True if green agent acknowledged the start signal, False otherwise
    """
    backend_url = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:9000")
    green_agent_url = green_agent["register_info"]["agent_url"]
    green_agent_name = green_agent.get("register_info", {}).get("alias", "green_agent")
    
    # Prepare red agent names mapping
    red_agent_names = {}
    for op_info in opponent_info_for_green:
        if op_info.get("agent_url"):
            red_agent_names[op_info["agent_url"]] = op_info.get("name", "red_agent")
    
    notify_success = await a2a_utils.notify_green_agent(
        green_agent_url,
        opponent_info_for_green,
        battle_id,
        backend_url=backend_url,
        green_agent_name=green_agent_name,
        red_agent_names=red_agent_names
    )
    
    if not notify_success:
        error_msg = "Failed to notify green agent to start battle"
        logger.error(f"Battle {battle_id}: {error_msg}")
        await _finish_battle_with_error(battle_id, error_msg)
        return False
        
    logger.info(f"Battle {battle_id}: Green agent notified to start battle")
    return True
