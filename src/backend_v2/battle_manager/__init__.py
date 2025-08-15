# -*- coding: utf-8 -*-

"""
Battle Manager Package for AgentBeats Backend V2.

This package contains the battle management system including:
- BattleManager: Queue and execution management
- Battle processors: Core battle execution logic
"""

from .manager import BattleManager, BattleState
from .processor import process_battle

__all__ = [
    "BattleManager",
    "BattleState", 
    "process_battle"
]
