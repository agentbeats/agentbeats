# -*- coding: utf-8 -*-

"""
models/battles.py - Defines the data models for battles in the backend.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class BattleState(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"


# Base Battle Models
class BattleBase(BaseModel):
    green_agent_id: str = Field(..., description="Green agent (judge/coordinator) ID")
    opponents: List[Dict[str, Any]] = Field(..., description="List of opponent agents with names and IDs")


class BattleCreateRequest(BaseModel):
    """Request model for creating a new battle"""
    green_agent_id: str = Field(..., description="Green agent (judge/coordinator) ID")
    opponents: List[Dict[str, Any]] = Field(..., description="List of opponent agents with names and IDs")
    config: Optional[Dict[str, Any]] = Field(None, description="Battle configuration")
    created_by: Optional[str] = Field(None, description="User who created this battle")


class BattleUpdateRequest(BaseModel):
    """Request model for updating a battle"""
    state: Optional[BattleState] = Field(None, description="Battle state")
    interact_history: Optional[List[Dict[str, Any]]] = Field(None, description="Interaction history (JSON)")
    result: Optional[Dict[str, Any]] = Field(None, description="Battle result (JSON)")
    error: Optional[str] = Field(None, description="Error message if battle failed")
    finished_at: Optional[datetime] = Field(None, description="Battle finish timestamp")


class BattleResponse(BaseModel):
    """Response model for battle data"""
    battle_id: str = Field(..., description="Unique battle identifier")
    green_agent_id: str = Field(..., description="Green agent (judge/coordinator) ID")
    opponents: List[Dict[str, Any]] = Field(..., description="List of opponent agents with names and IDs")
    user_id: str = Field(..., description="User who created this battle")
    created_at: datetime = Field(..., description="Battle creation timestamp")
    state: BattleState = Field(BattleState.PENDING, description="Current battle state")
    interact_history: Optional[List[Dict[str, Any]]] = Field(None, description="Interaction history (JSON)")
    finished_at: Optional[datetime] = Field(None, description="Battle finish timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Battle result (JSON)")
    error: Optional[str] = Field(None, description="Error message if battle failed")
    queue_position: Optional[int] = Field(None, description="Position in battle queue (runtime only)")


class BattleUpdateResponse(BaseModel):
    """Response model for battle updates"""
    battle_id: str = Field(..., description="Updated battle ID")
    message: str = Field(..., description="Update status message")
    state: BattleState = Field(..., description="Current battle state")


class BattleListResponse(BaseModel):
    """Response model for listing battles"""
    battles: List[BattleResponse]
