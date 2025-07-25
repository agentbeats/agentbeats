# -*- coding: utf-8 -*-
"""
Battle context management for AgentBeats logging.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class BattleContext:
    """Battle context for logging operations."""
    battle_id: str
    backend_url: str
    agent_name: str
    
    def __post_init__(self):
        """Validate and setup context after initialization."""
        logger.info(f"Battle context created for battle {self.battle_id} with agent {self.agent_name}") 