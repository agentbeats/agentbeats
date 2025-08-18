# -*- coding: utf-8 -*-

"""
models/__init__.py - Exports all models used in the backend.
"""

from .agents import (
    AgentCreateRequest,
    AgentResponse,
    AgentListResponse,
    AgentCardStatus, 
)
from .agent_instances import (
    AgentInstanceCreateRequest,
    AgentInstanceUpdateRequest,
    AgentInstanceResponse,
    AgentInstanceListResponse,
    AgentInstanceUpdateResponse,
)
from .battles import (
    BattleCreateRequest,
    BattleResponse,
    BattleListResponse,
    BattleUpdateRequest,
    BattleUpdateResponse,
)

__all__ = [
    # Agents
    "AgentCreateRequest",
    "AgentResponse",
    "AgentListResponse",
    "AgentCardStatus",

    # Agent Instances
    "AgentInstanceCreateRequest",
    "AgentInstanceUpdateRequest",
    "AgentInstanceResponse",
    "AgentInstanceListResponse",
    "AgentInstanceUpdateResponse",

    # Battles
    "BattleResponse",
    "BattleListResponse",
    "BattleUpdateResponse",
    "BattleCreateRequest",
    "BattleUpdateRequest",
]
