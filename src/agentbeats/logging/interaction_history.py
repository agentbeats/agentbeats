# -*- coding: utf-8 -*-
"""
Interaction history utilities for AgentBeats scenarios.
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Import context management
from .context import BattleContext


def _make_api_request(context: BattleContext, endpoint: str, data: Dict[str, Any]) -> bool:
    """Make API request to backend and return success status."""
    try:
        response = requests.post(
            f"{context.backend_url}/battles/{context.battle_id}/{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return response.status_code == 204
    except requests.exceptions.RequestException as e:
        logger.error("Network error when recording to backend for battle %s: %s", context.battle_id, str(e))
        return False


def record_battle_event(context: BattleContext, message: str, reported_by: str, detail: Optional[Dict[str, Any]] = None) -> str:
    """Record a battle event to the backend API and console."""
    event_data: Dict[str, Any] = {
        "event_type": "battle_event",
        "message": message,
        "reported_by": reported_by,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if detail:
        event_data["detail"] = detail
    
    if _make_api_request(context, "events", event_data):
        logger.info("Successfully recorded battle event for battle %s", context.battle_id)
        return 'event recorded to backend'
    else:
        return 'event recording failed'


def record_battle_result(context: BattleContext, message: str, winner: str, detail: Optional[Dict[str, Any]] = None) -> str:
    """Record the final battle result to backend API."""
    logger.info("Recording battle result for %s: winner=%s", context.battle_id, winner)
    
    result_data: Dict[str, Any] = {
        "event_type": "battle_result",
        "message": message,
        "winner": winner,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reported_by": "green_agent"
    }
    if detail:
        result_data["detail"] = detail
    
    if _make_api_request(context, "result", result_data):
        logger.info("Successfully recorded battle result to backend for battle %s", context.battle_id)
        return f'battle result recorded: winner={winner}'
    else:
        return 'result recording failed'


def record_agent_action(context: BattleContext, action: str, agent_name: str, detail: Optional[Dict[str, Any]] = None, interaction_details: Optional[Dict[str, Any]] = None) -> str:
    """Record an agent action to the backend API and console."""
    action_data: Dict[str, Any] = {
        "event_type": "agent_action",
        "action": action,
        "agent_name": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if detail:
        action_data["detail"] = detail
    if interaction_details:
        action_data["interaction_details"] = interaction_details
    
    if _make_api_request(context, "actions", action_data):
        logger.info("Successfully recorded agent action for battle %s", context.battle_id)
        return 'action recorded to backend'
    else:
        return 'action recording failed' 