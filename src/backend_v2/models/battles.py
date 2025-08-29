# -*- coding: utf-8 -*-

"""
models/battles.py - Defines the data models for battles in the backend.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# ===== API Models for Battles =====


class BattleState(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"
    CANCELLED = "cancelled"


class ParticipantRequirement(BaseModel):
    """Model for participant requirements"""
    name: str = Field(..., description="Name of the requirement")
    required: bool = Field(True, description="Whether the requirement is mandatory")
    role: str = Field(..., description="Role of the participant (e.g., 'red', 'blue')")

class Participant(BaseModel):
    """Model for battle participants"""
    name: str = Field(..., description="Name of the participant (e.g., 'red')")
    agent_id: str = Field(..., description="Agent ID of the participant")


# Base Battle Models
class BattleBase(BaseModel):
    green_agent_id: str = Field(..., description="Green agent (judge/coordinator) ID")
    participants: List[Participant] = Field(..., description="List of battle participants")


class BattleCreateRequest(BaseModel):
    """Request model for creating a new battle"""
    green_agent_id: str = Field(..., description="Green agent (judge/coordinator) ID")
    participants: List[Participant] = Field(..., description="List of battle participants")
    # TODO: config field for Luke's agent, will be implemented later
    config: Optional[Dict[str, Any]] = Field(None, description="Battle configuration")
    user_id: Optional[str] = Field(None, description="User who created this battle")


class BattleUpdateRequest(BaseModel):
    """Request model for updating a battle"""
    state: Optional[BattleState] = Field(None, description="Battle state")
    started_at: Optional[datetime] = Field(None, description="Battle start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Battle finish timestamp")
    interact_history: Optional[List[Dict[str, Any]]] = Field(None, description="Interaction history (JSON)")
    result: Optional[Dict[str, Any]] = Field(None, description="Battle result (JSON)")
    error: Optional[str] = Field(None, description="Error message if battle failed")


class BattleResponse(BaseModel):
    """Response model for battle data"""
    battle_id: str = Field(..., description="Unique battle identifier")
    green_agent_id: str = Field(..., description="Green agent (judge/coordinator) ID")
    participants: List[Participant] = Field(..., description="List of battle participants")
    user_id: str = Field(..., description="User who created this battle")
    created_at: datetime = Field(..., description="Battle creation timestamp")
    state: BattleState = Field(BattleState.PENDING, description="Current battle state")
    started_at: Optional[datetime] = Field(None, description="Battle start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Battle finish timestamp")
    interact_history: Optional[List[Dict[str, Any]]] = Field(None, description="Interaction history (JSON)")
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


# ===== Internal Model for Battle Manager =====


class BattleRecord(BaseModel):
    """Internal model for battle records in manager"""
    battle_id: str = Field(..., description="Unique battle identifier")
    green_agent_id: str = Field(..., description="Green agent (judge/coordinator) ID")
    participants: List[Participant] = Field(..., description="List of battle participants")
    # TODO: config field inherited from BattleCreateRequest, will be implemented later
    config: Optional[Dict[str, Any]] = Field(None, description="Battle configuration")
    user_id: Optional[str] = Field(None, description="User who created this battle")
    created_at: datetime = Field(..., description="Battle creation timestamp")
    state: BattleState = Field(BattleState.PENDING, description="Current battle state")
    started_at: Optional[datetime] = Field(None, description="Battle start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Battle finish timestamp")
    error: Optional[str] = Field(None, description="Error message if battle failed")

