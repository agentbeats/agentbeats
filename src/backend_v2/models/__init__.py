# -*- coding: utf-8 -*-

"""
models/__init__.py - Exports all models used in the backend.
"""

from .agents import (
    AgentCreateRequest,
    AgentResponse,
    AgentListResponse,
    AgentDeleteResponse,
    AgentCardStatus, 
)
from .agent_instances import (
    AgentInstanceHostedCreateRequest,
    AgentInstanceUpdateRequest,
    AgentInstanceResponse,
    AgentInstanceListResponse,
    AgentInstanceUpdateResponse,
    AgentInstanceDeleteResponse,
    AgentInstanceLogResponse,
    AgentInstanceDockerStatus,
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
    "AgentDeleteResponse",
    "AgentCardStatus",

    # Agent Instances
    "AgentInstanceHostedCreateRequest",
    "AgentInstanceUpdateRequest",
    "AgentInstanceResponse",
    "AgentInstanceListResponse",
    "AgentInstanceUpdateResponse",
    "AgentInstanceDeleteResponse",
    "AgentInstanceLogResponse",
    "AgentInstanceDockerStatus",

    # Battles
    "BattleResponse",
    "BattleListResponse",
    "BattleUpdateResponse",
    "BattleCreateRequest",
    "BattleUpdateRequest",
]
