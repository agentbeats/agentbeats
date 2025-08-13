# -*- coding: utf-8 -*-
"""
AgentInstance models for AgentBeats API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class InstanceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


# Agent Instance Models
class AgentInstanceBase(BaseModel):
    name: str = Field(..., description="Instance name")
    agent_id: str = Field(..., description="Parent agent group ID")
    launcher_config: Optional[Dict[str, Any]] = Field(None, description="Launcher configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Instance metadata")


class AgentInstanceCreateRequest(AgentInstanceBase):
    pass


class AgentInstanceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Instance name")
    status: Optional[InstanceStatus] = Field(None, description="Instance status")
    launcher_config: Optional[Dict[str, Any]] = Field(None, description="Launcher configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Instance metadata")


class AgentInstanceResponse(AgentInstanceBase):
    id: str = Field(..., description="Instance ID")
    status: InstanceStatus = Field(..., description="Instance status")
    endpoint_url: Optional[str] = Field(None, description="Instance endpoint URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_seen: Optional[datetime] = Field(None, description="Last activity timestamp")

    class Config:
        from_attributes = True


# Response Models
class AgentInstanceListResponse(BaseModel):
    instances: List[AgentInstanceResponse]
    total: int
