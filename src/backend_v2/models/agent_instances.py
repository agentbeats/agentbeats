# -*- coding: utf-8 -*-

"""
AgentInstance models for AgentBeats API.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Base Agent Instance Models
class AgentInstanceBase(BaseModel):
    agent_id: str = Field(..., description="Parent agent ID")
    agent_url: str = Field(..., description="Agent URL endpoint")
    launcher_url: str = Field(..., description="Launcher URL endpoint")


class AgentInstanceCreateRequest(AgentInstanceBase):
    """Request model for creating a new agent instance"""
    pass


class AgentInstanceUpdateRequest(BaseModel):
    """Request model for updating an agent instance"""
    agent_url: Optional[str] = Field(None, description="Agent URL endpoint")
    launcher_url: Optional[str] = Field(None, description="Launcher URL endpoint")
    is_locked: Optional[bool] = Field(None, description="Whether instance is locked for battle")
    ready: Optional[bool] = Field(None, description="Whether instance is ready")


class AgentInstanceResponse(AgentInstanceBase):
    """Response model for agent instance data"""
    agent_instance_id: str = Field(..., description="Unique agent instance identifier")
    is_locked: bool = Field(False, description="Whether instance is locked for battle")
    ready: bool = Field(False, description="Whether instance is ready")
    created_at: datetime = Field(..., description="Creation timestamp")


class AgentInstanceUpdateResponse(BaseModel):
    """Response model for agent instance updates"""
    agent_instance_id: str = Field(..., description="Updated agent instance ID")
    message: str = Field(..., description="Update status message")


class AgentInstanceListResponse(BaseModel):
    """Response model for listing agent instances"""
    instances: List[AgentInstanceResponse]
