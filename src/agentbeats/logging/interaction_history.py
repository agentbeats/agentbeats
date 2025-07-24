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

def record_battle_event(
    context: BattleContext,
    message: str,
    detail: Optional[Dict[str, Any]] = None
) -> str:
    """Record a battle event to the backend server."""
    event_data = {
        "is_result": False,
        "message": message,
        "reported_by": context.agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "detail": detail or {},
    }
    try:
        response = requests.post(
            f"{context.backend_url}/battles/{context.battle_id}",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 204:
            logger.info("Successfully recorded battle event to backend for battle %s", context.battle_id)
            return 'event recorded to backend'
        else:
            logger.error("Failed to record battle event to backend for battle %s: %s", context.battle_id, response.text)
            return 'event recording to backend failed'
    except Exception as e:
        logger.error("Exception recording battle event to backend for battle %s: %s", context.battle_id, str(e))
        return 'event recording to backend failed'


def record_battle_result(
    context: BattleContext,
    message: str,
    winner: str,
    detail: Optional[Dict[str, Any]] = None
) -> str:
    """Record the final battle result to the backend server."""
    result_data = {
        "is_result": True,
        "message": message,
        "winner": winner,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reported_by": context.agent_name,
        "detail": detail or {},
    }
    try:
        response = requests.post(
            f"{context.backend_url}/battles/{context.battle_id}",
            json=result_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 204:
            logger.info("Successfully recorded battle result to backend for battle %s", context.battle_id)
            return f'battle result recorded to backend: winner={winner}'
        else:
            logger.error("Failed to record battle result to backend for battle %s: %s", context.battle_id, response.text)
            return 'result recording to backend failed'
    except Exception as e:
        logger.error("Exception recording battle result to backend for battle %s: %s", context.battle_id, str(e))
        return 'result recording to backend failed'


def record_agent_action(
    context: BattleContext,
    action: str,
    detail: Optional[Dict[str, Any]] = None,
    interaction_details: Optional[Dict[str, Any]] = None
) -> str:
    """Record an agent action to the backend server."""
    event_data = {
        "is_result": False,
        "message": action,
        "reported_by": context.agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "detail": detail or {},
        "interaction_details": interaction_details or {},
    }
    try:
        response = requests.post(
            f"{context.backend_url}/battles/{context.battle_id}",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 204:
            logger.info("Successfully recorded agent action to backend for battle %s", context.battle_id)
            return 'action recorded to backend'
        else:
            logger.error("Failed to record agent action to backend for battle %s: %s", context.battle_id, response.text)
            return 'action recording to backend failed'
    except Exception as e:
        logger.error("Exception recording agent action to backend for battle %s: %s", context.battle_id, str(e))
        return 'action recording to backend failed' 