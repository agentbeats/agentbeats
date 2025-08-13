# -*- coding: utf-8 -*-

from fastapi import APIRouter, Path, Query
from typing import Optional

from ..models import (
    AgentCreateRequest,
    AgentResponse,
    AgentListResponse,
    AgentInstanceCreateRequest,
    AgentInstanceResponse,
    AgentInstanceListResponse,
)


router = APIRouter()


@router.post("/agents", response_model=AgentResponse, tags=["Agents"])
async def register_agent(agent: AgentCreateRequest):
    """Register a new agent"""
    # TODO: refer to backend_v1/agents.py: @router.get("/agents")


@router.get("/agents", response_model=AgentListResponse, tags=["Agents"])
async def list_all_agents(
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """List all agents (with ownership filtering)
       example: /api/agents?user_id=1234-12345-1234-1234567890ab"""
    # TODO: refer to backend_v1/agents.py: @router.get("/agents")


@router.get("/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def get_agent(
    agent_id: str = Path(..., description="Agent ID")
):
    """Get specific agent details"""
    # TODO: refer to backend_v1/agents.py: @router.get("/agents/{agent_id}")


@router.delete("/agents/{agent_id}", tags=["Agents"])
async def delete_agent(
    agent_id: str = Path(..., description="Agent ID")
):
    """Delete agent and all its instances"""
    # TODO: refer to backend_v1/agents.py: @router.delete("/agents/{agent_id}")


@router.get("/agents/{agent_id}/instances", response_model=AgentInstanceListResponse, tags=["Agents"])
async def list_agent_instances(
    agent_id: str = Path(..., description="Agent ID")
):
    """List all instances for a specific agent"""
    # TODO: no reference


@router.post("/agents/{agent_id}/instances", response_model=AgentInstanceResponse, tags=["Agents"])
async def create_hosted_agent_instance(
    agent_id: str = Path(..., description="Agent ID"),
    instance: AgentInstanceCreateRequest = None
):
    """Create new agent instance for hosted agent"""
    # TODO: no reference
