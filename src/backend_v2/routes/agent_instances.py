# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi import Path as FastAPIPath
from typing import Optional, Dict, Any
from pathlib import Path as FilePath
import subprocess
import threading

from ..models import (
    AgentInstanceUpdateRequest,
    AgentInstanceResponse,
    AgentInstanceListResponse,
    AgentInstanceUpdateResponse,
    AgentInstanceDeleteResponse,
    AgentInstanceLogResponse,
    AgentInstanceDockerStatus,
)
from ..db import instance_repo, agent_repo
from ..utils.auth import get_current_user
from ..utils.agent_utils import stop_hosted_agent_instance, read_file_log, read_live_docker_log

router = APIRouter()


@router.get("/agent_instances", response_model=AgentInstanceListResponse, tags=["AgentInstances"], status_code=status.HTTP_200_OK)
async def list_all_agent_instances(
    is_locked: Optional[bool] = Query(None, description="Filter by locked status"),
    ready: Optional[bool] = Query(None, description="Filter by ready status"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all agent instances
       example: /api/agent_instances?is_locked=false&ready=true"""
    try:
        instances = instance_repo.list_agent_instances(is_locked=is_locked, ready=ready)
        
        instance_responses = [AgentInstanceResponse(**instance) for instance in instances]
        
        return AgentInstanceListResponse(instances=instance_responses)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent instances: {str(e)}"
        )


@router.get("/agent_instances/{agent_instance_id}", response_model=AgentInstanceResponse, tags=["AgentInstances"], status_code=status.HTTP_200_OK)
async def get_agent_instance(
    agent_instance_id: str = FastAPIPath(..., description="Agent instance ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve a single agent instance"""
    try:
        instance = instance_repo.get_agent_instance(agent_instance_id)
        
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent instance with ID {agent_instance_id} not found"
            )
        
        return AgentInstanceResponse(**instance)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent instance: {str(e)}"
        )


@router.get("/agent_instances/hosted/{agent_instance_id}/logs/{log_type}", response_model=AgentInstanceLogResponse, tags=["AgentInstances"], status_code=status.HTTP_200_OK)
async def get_agent_instance_logs(
    agent_instance_id: str = FastAPIPath(..., description="Agent instance ID"),
    log_type: str = FastAPIPath(..., description="Log type: deployment, stop, or live_output"),
    lines: int = Query(100, description="Number of lines to fetch from the end (for live_output only)", ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get logs for a hosted agent instance"""
    try:
        # Validate log type
        valid_log_types = ["deployment", "stop", "live_output"]
        if log_type not in valid_log_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log type '{log_type}'. Must be one of: {', '.join(valid_log_types)}"
            )
        
        # Check if instance exists
        instance = instance_repo.get_agent_instance(agent_instance_id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent instance with ID {agent_instance_id} not found"
            )
        
        # Get the parent agent to check if it's hosted
        agent_id = instance.get('agent_id')
        agent = agent_repo.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent agent with ID {agent_id} not found"
            )
        
        is_hosted = agent.get('is_hosted', False)
        
        # Only return logs for hosted agents
        if not is_hosted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logs are only available for hosted agents"
            )
        
        if log_type == "live_output":
            # Read live Docker logs
            log_content, container_exists, container_name = read_live_docker_log(agent_instance_id, lines)
            
            return AgentInstanceLogResponse(
                agent_instance_id=agent_instance_id,
                log_type=log_type,
                log_content=log_content,
                is_hosted=is_hosted,
                container_name=container_name,
                container_exists=container_exists
            )
        else:
            # Read file-based logs (deployment or stop)
            log_content, log_exists = read_file_log(agent_instance_id, log_type)
            
            return AgentInstanceLogResponse(
                agent_instance_id=agent_instance_id,
                log_type=log_type,
                log_content=log_content,
                is_hosted=is_hosted,
                log_exists=log_exists
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving {log_type} logs: {str(e)}"
        )


@router.delete("/agent_instances/hosted/{agent_instance_id}", response_model=AgentInstanceDeleteResponse, tags=["AgentInstances"], status_code=status.HTTP_200_OK)
async def delete_hosted_agent_instance(
    agent_instance_id: str = FastAPIPath(..., description="Agent instance ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific agent instance"""
    try:
        # Check if instance exists
        instance = instance_repo.get_agent_instance(agent_instance_id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent instance with ID {agent_instance_id} not found"
            )
        
        # Check if instance is locked (cannot delete locked instances)
        if instance.get('is_locked', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete locked agent instance. Unlock it first."
            )
        
        # Get the parent agent to check if it's hosted
        agent_id = instance.get('agent_id')
        agent = agent_repo.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent agent with ID {agent_id} not found"
            )
        
        is_hosted = agent.get('is_hosted', False)
        
        if not is_hosted:
            # Remote agents: cannot delete instance directly
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete remote agent instances directly. Delete the parent agent instead."
            )
        
        # For hosted agents: update status to STOPPING and start background deletion
        try:
            # Update docker status to STOPPING
            instance_repo.update_agent_instance(agent_instance_id, {'docker_status': AgentInstanceDockerStatus.STOPPING})
            
            # Start background thread to stop Docker container and delete from database
            threading.Thread(
                target=stop_hosted_agent_instance,
                args=(agent_instance_id,),
                daemon=True
            ).start()
            
            return AgentInstanceDeleteResponse(
                agent_instance_id=agent_instance_id,
                message=f"Hosted agent instance {agent_instance_id} deletion initiated. Docker container is being stopped in background.",
                is_hosted=True,
                docker_stopping=True
            )
            
        except Exception as update_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate agent instance deletion: {str(update_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting agent instance: {str(e)}"
        )


@router.put("/agent_instances/{agent_instance_id}", response_model=AgentInstanceUpdateResponse, tags=["AgentInstances"], status_code=status.HTTP_200_OK)
async def update_agent_instance(
    update_data: AgentInstanceUpdateRequest,
    agent_instance_id: str = FastAPIPath(..., description="Agent instance ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update agent instance ready status"""
    try:
        # Check if instance exists
        instance = instance_repo.get_agent_instance(agent_instance_id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent instance with ID {agent_instance_id} not found"
            )
        
        # Prepare update data
        update_dict = {"ready": update_data.ready}
        
        # Update the instance
        updated_instance = instance_repo.update_agent_instance(agent_instance_id, update_dict)
        
        if not updated_instance:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update agent instance"
            )
        
        return AgentInstanceUpdateResponse(
            agent_instance_id=agent_instance_id,
            message=f"Agent instance ready status updated to {update_data.ready}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent instance: {str(e)}"
        )
