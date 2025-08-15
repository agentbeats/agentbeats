# -*- coding: utf-8 -*-
"""
Battle context management for AgentBeats logging.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any

logger = logging.getLogger(__name__)
_BATTLE_CONTEXT: Dict[str, Any] = {}


def set_battle_context(context: Dict):
    """
    Set the global battle context.
    """
    global _BATTLE_CONTEXT
    _BATTLE_CONTEXT = context


def get_battle_context() -> Dict:
    """
    Get the global battle context.
    """
    return _BATTLE_CONTEXT


def get_battle_id() -> str:
    """
    Get the global battle ID.
    """
    return _BATTLE_CONTEXT.get("battle_id")


def get_agent_id() -> str:
    """
    Get the global agent ID.
    """
    return _BATTLE_CONTEXT.get("agent_id")


def get_frontend_agent_name() -> str:
    """
    Get the global frontend agent name.
    """
    return _BATTLE_CONTEXT.get("frontend_agent_name")


def get_backend_url() -> str:
    """
    Get the global backend URL.
    """
    return _BATTLE_CONTEXT.get("backend_url")


# warning: I think Daniel is using this class somewhere, but I need new fields.
# To keep backward compatibility (e.g init failure), I will not change the class, but use my own new one.
@dataclass
class BattleContext:
    """Battle context for logging operations."""
    battle_id: str
    backend_url: str
    agent_name: str
    task_config: str = ""
    
    def __post_init__(self):
        """Validate and setup context after initialization."""
        logger.info(f"Battle context created for battle {self.battle_id} with agent {self.agent_name}") 