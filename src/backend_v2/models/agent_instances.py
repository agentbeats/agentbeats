# -*- coding: utf-8 -*-

"""
AgentInstance models for AgentBeats API.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class AgentInstanceDockerStatus(str, Enum):
    """Docker container status enum"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


# Base Agent Instance Models
class AgentInstanceBase(BaseModel):
    agent_id: str = Field(..., description="Parent agent ID")
    agent_url: str = Field(..., description="Agent URL endpoint")
    launcher_url: str = Field(..., description="Launcher URL endpoint")


class AgentInstanceHostedCreateRequest(BaseModel):
    """Request model for creating a new hosted agent instance"""
    pass


class AgentInstanceUpdateRequest(BaseModel):
    """Request model for updating an agent instance"""
    ready: bool = Field(..., description="Whether instance is ready")


class AgentInstanceResponse(AgentInstanceBase):
    """Response model for agent instance data"""
    agent_instance_id: str = Field(..., description="Unique agent instance identifier")
    is_locked: bool = Field(False, description="Whether instance is locked for battle")
    ready: bool = Field(False, description="Whether instance is ready")
    docker_status: AgentInstanceDockerStatus = Field(..., description="Docker container status")
    created_at: datetime = Field(..., description="Creation timestamp")


class AgentInstanceUpdateResponse(BaseModel):
    """Response model for agent instance updates"""
    agent_instance_id: str = Field(..., description="Updated agent instance ID")
    message: str = Field(..., description="Update status message")


class AgentInstanceDeleteResponse(BaseModel):
    """Response model for agent instance deletion"""
    agent_instance_id: str = Field(..., description="Deleted agent instance ID")
    message: str = Field(..., description="Deletion status message")
    is_hosted: bool = Field(..., description="Whether this was a hosted agent instance")
    docker_stopping: bool = Field(False, description="Whether Docker container is being stopped in background")


class AgentInstanceListResponse(BaseModel):
    """Response model for listing agent instances"""
    instances: List[AgentInstanceResponse]


class AgentInstanceLogResponse(BaseModel):
    """Unified response model for agent instance logs"""
    agent_instance_id: str = Field(..., description="Agent instance ID")
    log_type: str = Field(..., description="Type of log (deployment, stop, live_output)")
    log_content: str = Field(..., description="Log content")
    is_hosted: bool = Field(..., description="Whether this is a hosted agent instance")
    # Optional fields for different log types
    log_exists: Optional[bool] = Field(None, description="Whether log file exists (for file-based logs)")
    container_name: Optional[str] = Field(None, description="Docker container name (for live logs)")
    container_exists: Optional[bool] = Field(None, description="Whether Docker container exists (for live logs)")
    