# -*- coding: utf-8 -*-
"""
Agent communication utilities for AgentBeats scenarios.
"""

from .a2a import (
    create_a2a_client,
    send_message_to_agent,
    send_message_to_agents,
    send_messages_to_agents,
    get_agent_card,
    create_cached_a2a_client,
)

__all__ = [
    "create_a2a_client",
    "send_message_to_agent", 
    "send_message_to_agents",
    "send_messages_to_agents",
    "get_agent_card",
    "create_cached_a2a_client",
] 