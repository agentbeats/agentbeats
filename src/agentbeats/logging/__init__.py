# -*- coding: utf-8 -*-
"""
Logging utilities for AgentBeats scenarios.
"""

# Context management
from .context import BattleContext

# System logging functions
from .logging import (
    log_ready,
    log_error,
    log_startup,
    log_shutdown,
    update_battle_process
)

# Interaction history functions
from .interaction_history import (
    record_battle_event,
    record_battle_result,
    record_agent_action,
)

__all__ = [
    # Context management
    'BattleContext',
    
    # System logs
    'log_ready',
    'log_error',
    'log_startup',
    'log_shutdown',
    'update_battle_process',
    
    # Interaction history
    'record_battle_event',
    'record_battle_result',
    'record_agent_action',
] 