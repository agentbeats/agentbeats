# -*- coding: utf-8 -*-

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, status, Depends
from fastapi import Path as FastAPIPath

from ..models import (
    BattleCreateRequest,
    BattleResponse,
    BattleListResponse,
    BattleUpdateRequest,
    BattleUpdateResponse,
)
from ..utils.auth import *
from ..db import agent_repo, battle_repo
from ..battle_manager import BattleManager


router = APIRouter()

# Initialize battle manager (globally shared) and start it
battle_manager = BattleManager()
battle_manager.start()


@router.get("/battles", response_model=BattleListResponse, tags=["Battles"], status_code=status.HTTP_200_OK)
async def list_all_battles(
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """List all battles (with ownership filtering)
       example: /api/battles?user_id=1234-12345-1234-1234567890ab"""
    try:
        battles = battle_repo.list_battles(user_id=user_id)
        
        # Add queue position for queued battles
        response_battles = []
        for battle in battles:
            # Add queue position if battle is queued
            queue_position = None
            if battle.get('state') == 'queued':
                queue_position = battle_manager.get_queue_position(battle['battle_id'])
            
            # Add queue_position to battle data
            battle_with_queue = battle.copy()
            battle_with_queue['queue_position'] = queue_position
            
            # Ensure created_at is properly formatted for Pydantic
            if isinstance(battle_with_queue.get('created_at'), str):
                battle_with_queue['created_at'] = battle_with_queue['created_at'].replace('Z', '+00:00')
            
            # Ensure started_at is properly formatted for Pydantic
            if isinstance(battle_with_queue.get('started_at'), str):
                battle_with_queue['started_at'] = battle_with_queue['started_at'].replace('Z', '+00:00')
            
            # Ensure finished_at is properly formatted for Pydantic
            if isinstance(battle_with_queue.get('finished_at'), str):
                battle_with_queue['finished_at'] = battle_with_queue['finished_at'].replace('Z', '+00:00')
            
            response_battles.append(battle_with_queue)
        
        return BattleListResponse(battles=response_battles)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing battles: {str(e)}"
        )


@router.get("/battles/{battle_id}", response_model=BattleResponse, tags=["Battles"], status_code=status.HTTP_200_OK)
async def get_battle(
    battle_id: str = FastAPIPath(..., description="Battle ID")
):
    """Get specific battle details"""
    try:
        battle = battle_repo.get_battle(battle_id)
        
        if not battle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Battle with ID {battle_id} not found"
            )
        
        # Add queue position if battle is queued
        queue_position = None
        if battle.get('state') == 'queued':
            queue_position = battle_manager.get_queue_position(battle_id)
        
        # Add queue_position to battle data
        battle_with_queue = battle.copy()
        battle_with_queue['queue_position'] = queue_position
        
        # Ensure created_at is properly formatted for Pydantic
        if isinstance(battle_with_queue.get('created_at'), str):
            battle_with_queue['created_at'] = battle_with_queue['created_at'].replace('Z', '+00:00')
        
        # Ensure started_at is properly formatted for Pydantic
        if isinstance(battle_with_queue.get('started_at'), str):
            battle_with_queue['started_at'] = battle_with_queue['started_at'].replace('Z', '+00:00')
        
        # Ensure finished_at is properly formatted for Pydantic
        if isinstance(battle_with_queue.get('finished_at'), str):
            battle_with_queue['finished_at'] = battle_with_queue['finished_at'].replace('Z', '+00:00')
        
        return BattleResponse(**battle_with_queue)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving battle: {str(e)}"
        )


@router.post("/battles", response_model=BattleResponse, tags=["Battles"], status_code=status.HTTP_201_CREATED)
async def create_battle(
    battle_request: BattleCreateRequest, 
    user_id: Optional[str] = Depends(get_current_user)
):
    """Create a new battle"""
    try:
        # Convert to dict for easier handling
        battle_data = battle_request.model_dump()
        
        green_agent_id = battle_data['green_agent_id']
        participants = battle_data['participants']
        
        # Validate green agent exists
        green_agent = agent_repo.get_agent(green_agent_id)
        if not green_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Green agent with ID {green_agent_id} not found"
            )
        
        # Get participant requirements
        participant_requirements = green_agent.get("participant_requirements", [])
        participant_requirements_names = [p['name'] for p in participant_requirements]
        
        # Validate participants
        for participant in participants:
            if participant['name'] not in participant_requirements_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Participant {participant['name']}:{participant['agent_id']} does not match participant requirements"
                )
            
            # Validate participant agent exists
            participant_agent = agent_repo.get_agent(participant['agent_id'])
            if not participant_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant agent {participant['name']} with ID {participant['agent_id']} not found"
                )
        
        # Validate required participants are present
        for p_req in participant_requirements:
            if p_req.get('required', True) and not any(p['name'] == p_req['name'] for p in participants):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Required participant {p_req['name']} not found in participants"
                )
        
        # Create battle record for database
        battle_db_data = {
            'battle_id': str(uuid.uuid4()),
            'green_agent_id': green_agent_id,
            'participants': participants,
            'state': 'pending',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'user_id': battle_data.get('user_id', 'N/A'),
            'interact_history': [],
            'result': None,
            'error': None
        }
        
        # Save to database
        created_battle = battle_repo.create_battle(battle_db_data)
        
        # Add to battle manager queue - pass the validated request directly
        queue_position = battle_manager.add_battle(created_battle['battle_id'], battle_request)
        
        # Add queue_position to battle data and return
        created_battle['queue_position'] = queue_position
        
        # Ensure created_at is properly formatted for Pydantic
        if isinstance(created_battle.get('created_at'), str):
            created_battle['created_at'] = created_battle['created_at'].replace('Z', '+00:00')
        
        return BattleResponse(**created_battle)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating battle: {str(e)}"
        )


@router.post("/battles/{battle_id}", response_model=BattleUpdateResponse, tags=["Battles"], status_code=status.HTTP_200_OK)
async def update_battle(
    update_data: BattleUpdateRequest,
    battle_id: str = FastAPIPath(..., description="Battle ID")
):
    """Update an existing battle (handle battle result or log entry)"""
    try:
        # Get existing battle
        battle = battle_repo.get_battle(battle_id)
        if not battle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Battle with ID {battle_id} not found"
            )
        
        battle_state = battle.get("state", "finished")
        if battle_state == "finished":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Battle {battle_id} is not in a valid state for updates: {battle_state}"
            )
        
        # Prepare update fields based on provided data
        update_fields = {}
        
        # Update state if provided
        if update_data.state is not None:
            update_fields['state'] = update_data.state
        
        # Update started_at if provided
        if update_data.started_at is not None:
            update_fields['started_at'] = update_data.started_at.isoformat() + 'Z'
        
        # Update interact_history if provided
        if update_data.interact_history is not None:
            update_fields['interact_history'] = update_data.interact_history
        
        # Update result if provided
        if update_data.result is not None:
            update_fields['result'] = update_data.result
            # If result is provided, set state to finished
            update_fields['state'] = 'finished'
            if update_data.finished_at:
                update_fields['finished_at'] = update_data.finished_at.isoformat() + 'Z'
            else:
                update_fields['finished_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Update error if provided
        if update_data.error is not None:
            update_fields['error'] = update_data.error
            # If error is provided, set state to error
            update_fields['state'] = 'error'
        
        # Update finished_at if provided (and not already set by result)
        if update_data.finished_at is not None and 'finished_at' not in update_fields:
            update_fields['finished_at'] = update_data.finished_at.isoformat() + 'Z'
        
        
        # Update battle in database
        updated_battle = battle_repo.update_battle(battle_id, update_fields)
        
        if not updated_battle:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update battle"
            )
        
        # Update battle manager state if battle is finished
        if update_fields.get('state') == 'finished' and update_data.result is not None:
            battle_manager.finish_battle(battle_id, update_data.result)
        
        return BattleUpdateResponse(
            battle_id=battle_id,
            message="Battle updated successfully",
            state=updated_battle['state']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating battle: {str(e)}"
        )
