# -*- coding:utf-8 -*-

"""
db/__init__.py: Database initialization and repository setup.
"""

import os

from .repositories import (
    DatabaseManager,
    AgentRepository,
    AgentInstanceRepository,
    BattleRepository,
)


__all__ = [
    "agent_repo",
    "instance_repo",
    "battle_repo",
]


db_manager = DatabaseManager(os.path.join(os.path.dirname(__file__), 'data'))
agent_repo = AgentRepository(db_manager)
instance_repo = AgentInstanceRepository(db_manager)
battle_repo = BattleRepository(db_manager)
