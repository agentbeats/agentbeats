# -*- coding: utf-8 -*-
"""
Agent and AgentInstance models for AgentBeats API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    HOSTED = "hosted"
    EXTERNAL = "external"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


# Agent Models
class AgentBase(BaseModel):
    name: str = Field(..., description="Agent group name")
    description: Optional[str] = Field(None, description="Agent description")
    agent_type: AgentType = Field(..., description="Type of agent (hosted/external)")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")


class AgentCreateRequest(AgentBase):
    pass


class AgentResponse(AgentBase):
    id: str = Field(..., description="Agent group ID")
    status: AgentStatus = Field(..., description="Agent status")
    owner_id: Optional[str] = Field(None, description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    instance_count: int = Field(0, description="Number of instances")

    class Config:
        from_attributes = True


# Response Models
class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
