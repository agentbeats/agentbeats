# -*- coding: utf-8 -*-

import uuid
import threading

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi import Path as FastAPIPath # remark: to avoid the same name as Path Library
from ..models import (
    AgentCreateRequest,
    AgentResponse,
    AgentListResponse,
    AgentInstanceCreateRequest,
    AgentInstanceResponse,
    AgentInstanceListResponse,
    AgentCardStatus,
)
from ..db import agent_repo, instance_repo
from ..utils.auth import *
from ..utils.agent_utils import *


router = APIRouter()


@router.post("/agents", response_model=AgentResponse, tags=["Agents"], status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: AgentCreateRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create agent. If its a hosted agent, it will be created with no instance.
       If its a remote agent, it will be created with one instance."""
    try:
        # Remote agents must come with URLs
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
        agent_data['user_id'] = current_user['id']
        instance_fields = ['agent_url', 'launcher_url']
        instance_data = {k: agent_data.pop(k, None) for k in instance_fields}
        
        # Set initial agent card status and data based on agent type
        if request.is_hosted:
            # Hosted agents start with loading status and no card
            agent_data['agent_card_status'] = AgentCardStatus.LOADING
            agent_data['agent_card'] = None
            
            # Start background deployment for hosted agent
            if request.docker_image_link:
                threading.Thread(
                    target=deploy_hosted_agent,
                    args=(agent_data['agent_id'], request.docker_image_link),
                    daemon=True
                ).start()
        else:
            # Remote agents: try to fetch agent card immediately
            try:
                agent_url = instance_data.get('agent_url')
                if agent_url:
                    agent_card = await fetch_agent_card(agent_url, timeout=5.0)
                    if agent_card:
                        agent_data['agent_card_status'] = AgentCardStatus.READY
                        agent_data['agent_card'] = agent_card
                    else:
                        agent_data['agent_card_status'] = AgentCardStatus.ERROR
                        agent_data['agent_card'] = None
                else:
                    agent_data['agent_card_status'] = AgentCardStatus.ERROR
                    agent_data['agent_card'] = None
            except Exception as e:
                print(f"Failed to fetch agent card for {agent_url}: {str(e)}")
                agent_data['agent_card_status'] = AgentCardStatus.ERROR
                agent_data['agent_card'] = None
        
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
        
        # Remark: If this is a hosted agent, the instance will be created in the background
        
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
    scope: str = Query("all", description="Agent visibility scope: 'mine' for user agents only, 'all' for user + public + dev agents"),
    is_green: Optional[bool] = Query(None, description="Filter by green agent status"),
    check_liveness: bool = Query(False, description="Check agent liveness status"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all agents. Optionally filter by user or green status."""
    try:
        user_id = current_user['id']
        if scope == "mine":
            agents = agent_repo.list_agents(user_id=user_id, is_green=is_green)

        elif scope == "all":
            agents = agent_repo.list_agents(is_green=is_green)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid scope parameter. Use 'mine' or 'all'."
            )

        if check_liveness:
            agents = await check_agents_liveness(agents)
            
        agent_responses = [AgentResponse(**agent) for agent in agents]
        
        return AgentListResponse(agents=agent_responses)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agents: {str(e)}"
        )


@router.get("/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"], status_code=status.HTTP_200_OK)
async def get_agent(
    agent_id: str = FastAPIPath(..., description="Agent ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    agent_id: str = FastAPIPath(..., description="Agent ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
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

        agent_owner_id = agent.get('user_id')
        user_id = current_user['id']
        if user_id != "dev-user-id" and agent_owner_id != user_id: # dev user or owner can delete
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - can only delete your own agents"
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
    agent_id: str = FastAPIPath(..., description="Agent ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    agent_id: str = FastAPIPath(..., description="Agent ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
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
