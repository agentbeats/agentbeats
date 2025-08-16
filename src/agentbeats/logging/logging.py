# -*- coding: utf-8 -*-
"""
System logging utilities for AgentBeats scenarios.
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
_logger = logging.getLogger(__name__)

# Import context management
from .context import BattleContext


def update_battle_process(
    battle_id: str,
    backend_url: str,
    message: str,
    detail: dict = None,
    markdown_content: str = None,
    terminal_input: str = None,
    terminal_output: str = None,
    asciinema_url: str = None,
    reported_by: str = "agentbeats_sdk",
) -> str:
    """
    Log battle process updates to backend API.
    """
    event_data = {
        "is_result": False,
        "message": message,
        "reported_by": reported_by,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if detail:
        event_data["detail"] = detail

    if markdown_content:
        event_data["markdown_content"] = markdown_content

    if terminal_input and terminal_output:
        event_data["terminal_input"] = terminal_input
        event_data["terminal_output"] = terminal_output

    if asciinema_url:
        event_data["asciinema_url"] = asciinema_url

    try:
        requests.post(
            f"{backend_url}/battles/{battle_id}",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
    except Exception as e:
        _logger.error(
            "Error when recording to backend for battle %s: %s",
            battle_id,
            str(e),
        )
        return False


# Comment: Why do we have so many functions here?
# I think one unified function for logging events would be better.
# These are kept for any legacy use.


def _make_api_request(
    context: BattleContext, endpoint: str, data: Dict[str, Any]
) -> bool:
    """Make API request to backend and return success status."""
    try:
        response = requests.post(
            f"{context.backend_url}/battles/{context.battle_id}/{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return response.status_code == 204
    except requests.exceptions.RequestException as e:
        _logger.error(
            "Network error when recording to backend for battle %s: %s",
            context.battle_id,
            str(e),
        )
        return False


def log_ready(
    context: BattleContext, capabilities: Optional[Dict[str, Any]] = None
) -> str:
    """Log agent readiness to the backend API and console."""
    ready_data: Dict[str, Any] = {
        "event_type": "agent_ready",
        "agent_name": context.agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if capabilities:
        ready_data["capabilities"] = capabilities

    if _make_api_request(context, "ready", ready_data):
        _logger.info(
            "Successfully logged agent readiness for battle %s",
            context.battle_id,
        )
        return "readiness logged to backend"
    else:
        return "readiness logging failed"


def log_error(
    context: BattleContext, error_message: str, error_type: str = "error"
) -> str:
    """Log an error event to the backend API and console."""
    error_data: Dict[str, Any] = {
        "event_type": "error",
        "error_type": error_type,
        "error_message": error_message,
        "reported_by": context.agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if _make_api_request(context, "errors", error_data):
        _logger.error(
            "Successfully logged error to backend for battle %s",
            context.battle_id,
        )
        return "error logged to backend"
    else:
        return "error logging failed"


def log_startup(
    context: BattleContext, config: Optional[Dict[str, Any]] = None
) -> str:
    """Log agent startup to the backend API and console."""
    startup_data: Dict[str, Any] = {
        "event_type": "agent_startup",
        "agent_name": context.agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if config:
        startup_data["config"] = config

    if _make_api_request(context, "startup", startup_data):
        _logger.info(
            "Successfully logged agent startup for battle %s",
            context.battle_id,
        )
        return "startup logged to backend"
    else:
        return "startup logging failed"


def log_shutdown(context: BattleContext, reason: str = "normal") -> str:
    """Log agent shutdown to the backend API and console."""
    shutdown_data: Dict[str, Any] = {
        "event_type": "agent_shutdown",
        "agent_name": context.agent_name,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if _make_api_request(context, "shutdown", shutdown_data):
        _logger.info(
            "Successfully logged agent shutdown for battle %s",
            context.battle_id,
        )
        return "shutdown logged to backend"
    else:
        return "shutdown logging failed"
