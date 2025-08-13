# -*- coding: utf-8 -*-

from fastapi import APIRouter, Path, Query
from typing import Optional

from ..models import (
    BattleCreateRequest,
    BattleResponse,
    BattleListResponse,
    BattleUpdateRequest,
    BattleUpdateResponse,
)

router = APIRouter()


@router.get("/battles", response_model=BattleListResponse, tags=["Battles"])
async def list_all_battles(
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """List all battles (with ownership filtering)
       example: /api/battles?user_id=1234-12345-1234-1234567890ab"""
    # TODO: refer to backend_v1/battles.py: @router.get("/battles")


@router.get("/battles/{battle_id}", response_model=BattleResponse, tags=["Battles"])
async def get_battle(
    battle_id: str = Path(..., description="Battle ID")
):
    """Get specific battle details"""
    # TODO: refer to backend_v1/battles.py: @router.get("/battles/{battle_id}")


@router.post("/battles", response_model=BattleResponse, tags=["Battles"])
async def create_battle(
    battle: BattleCreateRequest
):
    """Create a new battle"""
    # TODO: refer to backend_v1/battles.py: @router.post("/battles")


@router.post("/battles/{battle_id}", response_model=BattleUpdateResponse, tags=["Battles"])
async def update_battle(
    battle_id: str = Path(..., description="Battle ID"),
    battle: BattleUpdateRequest = None
):
    """Update an existing battle"""
    # TODO: refer to backend_v1/battles.py: @router.post("/battles/{battle_id}")
