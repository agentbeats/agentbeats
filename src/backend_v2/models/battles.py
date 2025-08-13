# -*- coding: utf-8 -*-

"""
models/battles.py - Defines the data models for battles in the backend.
"""

from pydantic import BaseModel, Field


class BattleCreateRequest(BaseModel):
    """Request model for creating a new battle"""
    name: str = Field(..., description="Name of the battle")
    description: str = Field(None, description="Description of the battle")
    user_id: str = Field(..., description="ID of the user creating the battle")


class BattleResponse(BaseModel):
    """Response model for a battle"""
    id: str = Field(..., description="Unique identifier for the battle")
    name: str = Field(..., description="Name of the battle")
    description: str = Field(None, description="Description of the battle")
    user_id: str = Field(..., description="ID of the user who created the battle")


class BattleListResponse(BaseModel):
    """Response model for listing battles"""
    battles: list[BattleResponse] = Field(..., description="List of battles")
    total: int = Field(..., description="Total number of battles")


class BattleUpdateRequest(BaseModel):
    """Request model for updating a battle"""
    name: str = Field(None, description="Updated name of the battle")
    description: str = Field(None, description="Updated description of the battle")


class BattleUpdateResponse(BattleResponse):
    """Response model for updating a battle"""
    updated_at: str = Field(..., description="Timestamp of the last update to the battle")
    user_id: str = Field(..., description="ID of the user who updated the battle")
