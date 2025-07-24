# -*- coding: utf-8 -*-
"""
Agent communication utilities for AgentBeats scenarios.
"""

from .a2a import (
    create_a2a_client,
    send_message_to_agent,
    send_message_to_agents,
)

__all__ = [
    "create_a2a_client",
    "send_message_to_agent", 
    "send_message_to_agents",
] 