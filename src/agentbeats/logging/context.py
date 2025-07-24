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
    agent_name: str = "system"
    mcp_tools: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate and setup context after initialization."""
        if self.mcp_tools:
            logger.info(f"Battle context created with {len(self.mcp_tools)} MCP tools for {self.agent_name}")
        else:
            logger.info(f"Battle context created for {self.agent_name}") 