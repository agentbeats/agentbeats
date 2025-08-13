# -*- coding: utf-8 -*-

from fastapi import APIRouter, Path, Query
from typing import Optional

from ..models import (
    AgentInstanceUpdateRequest,
    AgentInstanceResponse,
    AgentInstanceListResponse,
    AgentInstanceUpdateResponse,
)


router = APIRouter()


@router.get("/agent_instances", response_model=AgentInstanceListResponse, tags=["AgentInstances"])
async def list_all_agent_instances(
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """List all agent instances
       example: /api/agent_instances?user_id=1234-12345-1234-1234567890ab"""
    # TODO: refer to backend_v1/agents.py: @router.get("/agents")


@router.get("/agent_instances/{agent_instance_id}", response_model=AgentInstanceResponse, tags=["AgentInstances"])
async def get_agent_instance(
    agent_instance_id: str = Path(..., description="Agent instance ID")
):
    """Retrieve a single agent instance"""
    # TODO: refer to backend_v1/agents.py: @router.get("/agents/{agent_id}")


@router.delete("/agent_instances/{agent_instance_id}", tags=["AgentInstances"])
async def delete_agent_instance(
    agent_instance_id: str = Path(..., description="Agent instance ID")
):
    """Delete a specific agent instance"""
    # TODO: refer to backend_v1/agents.py: @router.delete("/agents/{agent_id}")


@router.put("/agent_instances/{agent_instance_id}", response_model=AgentInstanceUpdateResponse, tags=["AgentInstances"])
async def update_agent_instance(
    agent_instance_id: str = Path(..., description="Agent instance ID"),
    update_data: AgentInstanceUpdateRequest = None
):
    """Update agent instance status or info"""
    # TODO: refer to backend_v1/agents.py: @router.put("/agents/{agent_id}")
