# -*- coding: utf-8 -*-

"""
Agent models for AgentBeats API.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentCardStatus(str, Enum):
    """Enum for agent card status."""
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class AgentBase(BaseModel):
    """Base model for agent data."""
    alias: str = Field(..., description="Agent alias/name")
    is_hosted: bool = Field(..., description="Whether this is a hosted agent")
    is_green: bool = Field(..., description="Whether this is a green agent (judge/coordinator)")
    battle_description: Optional[str] = Field(None, description="Battle description for selection UI")
    participant_requirements: Optional[List[Dict[str, Any]]] = Field(None, description="Participant requirements (JSON)")


class AgentCreateRequest(AgentBase):
    """Request model for creating a new agent"""

    user_id: str = Field(..., description="Owner user ID")

    # Will use is_hosted field to determine if this is a hosted agent
    # Which is inherited from AgentBase
    
    # Optional fields for remote agents (non-hosted)
    agent_url: Optional[str] = Field(None, description="Agent URL endpoint (required for remote agents)")
    launcher_url: Optional[str] = Field(None, description="Launcher URL endpoint (required for remote agents)")
    
    # Optional fields for hosted agents
    github_link: Optional[str] = Field(None, description="GitHub link for the hosted agent repository")


class AgentResponse(AgentBase):
    """Response model for agent data"""
    agent_id: str = Field(..., description="Unique agent identifier")
    user_id: str = Field(..., description="Owner user ID")
    elo: Optional[Dict[str, Any]] = Field(None, description="ELO rating data (JSON)")
    agent_card_status: AgentCardStatus = Field(..., description="Current status of the agent card")
    agent_card: Optional[Dict[str, Any]] = Field(None, description="Agent card data (JSON)")
    created_at: datetime = Field(..., description="Creation timestamp")


class AgentListResponse(BaseModel):
    """Response model for listing agents"""
    agents: List[AgentResponse]
