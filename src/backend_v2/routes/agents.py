# -*- coding: utf-8 -*-

import uuid

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path, Query, status
from ..models import (
    AgentCreateRequest,
    AgentResponse,
    AgentListResponse,
    AgentInstanceCreateRequest,
    AgentInstanceResponse,
    AgentInstanceListResponse,
)
from ..db import agent_repo, instance_repo


router = APIRouter()


@router.post("/agents", response_model=AgentResponse, tags=["Agents"], status_code=status.HTTP_201_CREATED)
async def register_agent(request: AgentCreateRequest):
    """Create agent. If its a hosted agent, it will be created with no instance.
       If its a remote agent, it will be created with one instance."""
    try:
        # Validate remote agent requirements
        if not request.is_hosted:
            if not request.agent_url or not request.launcher_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="agent_url and launcher_url are required for remote agents"
                )
        
        # Create agent data
        agent_data = request.model_dump()
        agent_data['agent_id'] = str(uuid.uuid4())
        agent_data['created_at'] = datetime.utcnow().isoformat() + 'Z'
        instance_fields = ['agent_url', 'launcher_url']
        instance_data = {k: agent_data.pop(k, None) for k in instance_fields}
        
        created_agent = agent_repo.create_agent(agent_data)
        
        if not created_agent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create agent due to database errors"
            )
        
        # If it's a remote agent (not hosted), create an instance automatically
        if not request.is_hosted:
            instance_create_data = {
                'agent_id': created_agent['agent_id'],
                'agent_url': instance_data['agent_url'],
                'launcher_url': instance_data['launcher_url'],
                'agent_instance_id': str(uuid.uuid4()),
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'is_locked': False,
                'ready': False
            }
            
            created_instance = instance_repo.create_agent_instance(instance_create_data)
            
            if not created_instance:
                # If instance creation fails, we should clean up the agent
                agent_repo.delete_agent(created_agent['agent_id'])
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create agent instance for remote agent due to database errors"
                )
        
        return AgentResponse(**created_agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating agent: {str(e)}"
        )


@router.get("/agents", response_model=AgentListResponse, tags=["Agents"], status_code=status.HTTP_200_OK)
async def list_all_agents(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    is_green: Optional[bool] = Query(None, description="Filter by green agent status")
):
    """List all agents (with ownership filtering)
       example: /api/agents?user_id=1234-12345-1234-1234567890ab&is_green=true"""
    try:
        agents = agent_repo.list_agents(user_id=user_id, is_green=is_green)
        
        agent_responses = [AgentResponse(**agent) for agent in agents]
        
        return AgentListResponse(agents=agent_responses)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agents: {str(e)}"
        )


@router.get("/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"], status_code=status.HTTP_200_OK)
async def get_agent(
    agent_id: str = Path(..., description="Agent ID")
):
    """Get specific agent details"""
    try:
        agent = agent_repo.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        return AgentResponse(**agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent: {str(e)}"
        )


@router.delete("/agents/{agent_id}", tags=["Agents"], status_code=status.HTTP_200_OK)
async def delete_agent(
    agent_id: str = Path(..., description="Agent ID")
):
    """Delete agent and all its instances"""
    try:
        # Check if agent exists
        agent = agent_repo.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        # Delete the agent (instances will be deleted via cascade)
        success = agent_repo.delete_agent(agent_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete agent"
            )

        success = instance_repo.delete_agent_instances_by_agent_id(agent_id)
        # TODO: delete all instance DOCKER files&process associated with this agent

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete agent instances"
            )
        
        return {"message": f"Agent {agent_id} and all its instances deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting agent: {str(e)}"
        )


@router.get("/agents/{agent_id}/instances", response_model=AgentInstanceListResponse, tags=["Agents"], status_code=status.HTTP_200_OK)
async def list_agent_instances(
    agent_id: str = Path(..., description="Agent ID")
):
    """List all instances for a specific agent"""
    try:
        # Check if agent exists
        agent = agent_repo.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        # Get instances for this agent
        instances = instance_repo.get_agent_instances_by_agent_id(agent_id)
        
        instance_responses = [AgentInstanceResponse(**instance) for instance in instances]
        
        return AgentInstanceListResponse(instances=instance_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent instances: {str(e)}"
        )


@router.post("/agents/{agent_id}/instances", response_model=AgentInstanceResponse, tags=["Agents"], status_code=status.HTTP_201_CREATED)
async def create_hosted_agent_instance(
    instance: AgentInstanceCreateRequest,
    agent_id: str = Path(..., description="Agent ID")
):
    """Create new agent instance for hosted agent"""
    try:
        # Check if agent exists
        agent = agent_repo.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        # Verify this is a hosted agent
        if not agent.get('is_hosted', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only create instances for hosted agents"
            )
        
        # Create instance data
        instance_data = instance.model_dump()
        instance_data['agent_id'] = agent_id
        instance_data['agent_instance_id'] = str(uuid.uuid4())
        instance_data['created_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Create the instance
        created_instance = instance_repo.create_agent_instance(instance_data)
        
        if not created_instance:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create agent instance"
            )
        
        return AgentInstanceResponse(**created_instance)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating agent instance: {str(e)}"
        )
