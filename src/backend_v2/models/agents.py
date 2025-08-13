# -*- coding: utf-8 -*-

"""
Agent models for AgentBeats API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Base Agent Models
class AgentBase(BaseModel):
    alias: str = Field(..., description="Agent alias/name")
    is_hosted: bool = Field(..., description="Whether this is a hosted agent")
    is_green: bool = Field(..., description="Whether this is a green agent (judge/coordinator)")
    battle_description: Optional[str] = Field(None, description="Battle description for selection UI")
    participant_requirements: Optional[List[Dict[str, Any]]] = Field(None, description="Participant requirements (JSON)")


class AgentCreateRequest(AgentBase):
    """Request model for creating a new agent"""
    pass


class AgentResponse(AgentBase):
    """Response model for agent data"""
    agent_id: str = Field(..., description="Unique agent identifier")
    user_id: str = Field(..., description="Owner user ID")
    elo: Optional[Dict[str, Any]] = Field(None, description="ELO rating data (JSON)")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Response model for listing agents"""
    agents: List[AgentResponse]
