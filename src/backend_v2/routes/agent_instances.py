# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Path, Query, status, Depends
from typing import Optional, Dict, Any

from ..models import (
    AgentInstanceUpdateRequest,
    AgentInstanceResponse,
    AgentInstanceListResponse,
    AgentInstanceUpdateResponse,
)
from ..db import instance_repo
from ..utils.auth import get_current_user

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
    agent_instance_id: str = Path(..., description="Agent instance ID"),
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


@router.delete("/agent_instances/{agent_instance_id}", tags=["AgentInstances"], status_code=status.HTTP_200_OK)
async def delete_agent_instance(
    agent_instance_id: str = Path(..., description="Agent instance ID"),
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
        
        # Delete the instance
        success = instance_repo.delete_agent_instance(agent_instance_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete agent instance"
            )
        
        return {"message": f"Agent instance {agent_instance_id} deleted successfully"}
        
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
    agent_instance_id: str = Path(..., description="Agent instance ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update agent instance status or info"""
    try:
        # Check if instance exists
        instance = instance_repo.get_agent_instance(agent_instance_id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent instance with ID {agent_instance_id} not found"
            )
        
        # Prepare update data, excluding None values
        update_dict = update_data.model_dump(exclude_none=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        # Update the instance
        updated_instance = instance_repo.update_agent_instance(agent_instance_id, update_dict)
        
        if not updated_instance:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update agent instance"
            )
        
        return AgentInstanceUpdateResponse(
            agent_instance_id=agent_instance_id,
            message="Agent instance updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent instance: {str(e)}"
        )
