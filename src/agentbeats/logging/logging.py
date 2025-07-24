# -*- coding: utf-8 -*-
"""
System logging utilities for AgentBeats scenarios.
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


def log_ready(context: BattleContext, agent_name: str, capabilities: Optional[Dict[str, Any]] = None) -> str:
    """Log agent readiness to the backend API and console."""
    ready_data: Dict[str, Any] = {
        "event_type": "agent_ready",
        "agent_name": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if capabilities:
        ready_data["capabilities"] = capabilities
    
    if _make_api_request(context, "ready", ready_data):
        logger.info("Successfully logged agent readiness for battle %s", context.battle_id)
        return 'readiness logged to backend'
    else:
        return 'readiness logging failed'


def log_error(context: BattleContext, error_message: str, error_type: str = "error", reported_by: str = "system") -> str:
    """Log an error event to the backend API and console."""
    error_data: Dict[str, Any] = {
        "event_type": "error",
        "error_type": error_type,
        "error_message": error_message,
        "reported_by": reported_by,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if _make_api_request(context, "errors", error_data):
        logger.error("Successfully logged error to backend for battle %s", context.battle_id)
        return 'error logged to backend'
    else:
        return 'error logging failed'


def log_startup(context: BattleContext, agent_name: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Log agent startup to the backend API and console."""
    startup_data: Dict[str, Any] = {
        "event_type": "agent_startup",
        "agent_name": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if config:
        startup_data["config"] = config
    
    if _make_api_request(context, "startup", startup_data):
        logger.info("Successfully logged agent startup for battle %s", context.battle_id)
        return 'startup logged to backend'
    else:
        return 'startup logging failed'


def log_shutdown(context: BattleContext, agent_name: str, reason: str = "normal") -> str:
    """Log agent shutdown to the backend API and console."""
    shutdown_data: Dict[str, Any] = {
        "event_type": "agent_shutdown",
        "agent_name": agent_name,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if _make_api_request(context, "shutdown", shutdown_data):
        logger.info("Successfully logged agent shutdown for battle %s", context.battle_id)
        return 'shutdown logged to backend'
    else:
        return 'shutdown logging failed' 