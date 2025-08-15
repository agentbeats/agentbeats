# -*- coding: utf-8 -*-

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Path, Query, HTTPException, status, Depends

from ..models import (
    BattleCreateRequest,
    BattleResponse,
    BattleListResponse,
    BattleUpdateRequest,
    BattleUpdateResponse,
)
from ..utils.auth import *
from ..db import agent_repo, battle_repo
from ..utils.battle_manager import BattleManager

router = APIRouter()

# Initialize battle manager (globally shared)
battle_manager = BattleManager()


@router.get("/battles", response_model=BattleListResponse, tags=["Battles"], status_code=status.HTTP_200_OK)
async def list_all_battles(
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """List all battles (with ownership filtering)
       example: /api/battles?user_id=1234-12345-1234-1234567890ab"""
    try:
        battles = battle_repo.list_battles(user_id=user_id)
        
        # Convert to response format
        response_battles = []
        for battle in battles:
            # Convert participant_ids back to opponents format for frontend
            participant_ids = battle.get('participant_ids', [])
            opponents = []
            
            # Try to get original opponents from battle manager or reconstruct
            battle_status = battle_manager.get_battle_status(battle['battle_id'])
            if battle_status and 'opponents' in battle_status:
                opponents = battle_status['opponents']
            else:
                # Fallback: create basic opponent structure
                for i, agent_id in enumerate(participant_ids):
                    opponents.append({
                        'agent_id': agent_id,
                        'name': f'opponent_{i+1}'  # Basic fallback name
                    })
            
            # Add queue position for queued battles
            queue_position = None
            if battle.get('state') == 'queued':
                queue_position = battle_manager.get_queue_position(battle['battle_id'])
            
            response_battle = {
                'battle_id': battle['battle_id'],
                'green_agent_id': battle['green_agent_id'],
                'opponents': opponents,
                'user_id': battle['user_id'],
                'created_at': battle['created_at'],
                'state': battle['state'],
                'interact_history': battle.get('interact_history'),
                'finished_at': battle.get('finished_at'),
                'result': battle.get('result'),
                'error': battle.get('error'),
                'queue_position': queue_position
            }
            response_battles.append(response_battle)
        
        return BattleListResponse(battles=response_battles)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing battles: {str(e)}"
        )


@router.get("/battles/{battle_id}", response_model=BattleResponse, tags=["Battles"], status_code=status.HTTP_200_OK)
async def get_battle(
    battle_id: str = Path(..., description="Battle ID")
):
    """Get specific battle details"""
    try:
        battle = battle_repo.get_battle(battle_id)
        
        if not battle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Battle with ID {battle_id} not found"
            )
        
        # Convert participant_ids back to opponents format for frontend
        participant_ids = battle.get('participant_ids', [])
        opponents = []
        
        # Try to get original opponents from battle manager
        battle_status = battle_manager.get_battle_status(battle_id)
        if battle_status and 'opponents' in battle_status:
            opponents = battle_status['opponents']
        else:
            # Fallback: create basic opponent structure
            for i, agent_id in enumerate(participant_ids):
                opponents.append({
                    'agent_id': agent_id,
                    'name': f'opponent_{i+1}'  # Basic fallback name
                })
        
        # Add queue position if battle is queued
        queue_position = None
        if battle.get('state') == 'queued':
            queue_position = battle_manager.get_queue_position(battle_id)
        
        response_data = {
            'battle_id': battle['battle_id'],
            'green_agent_id': battle['green_agent_id'],
            'opponents': opponents,
            'user_id': battle['user_id'],
            'created_at': battle['created_at'],
            'state': battle['state'],
            'interact_history': battle.get('interact_history'),
            'finished_at': battle.get('finished_at'),
            'result': battle.get('result'),
            'error': battle.get('error'),
            'queue_position': queue_position
        }
        
        return BattleResponse(**response_data)
    
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
        opponents = battle_data['opponents']
        
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
        
        # Validate opponents
        participant_ids = []
        
        for opponent in opponents:
            if not isinstance(opponent, dict) or 'name' not in opponent or 'agent_id' not in opponent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each opponent must be a dictionary with 'name' and 'agent_id'"
                )
            
            if opponent['name'] not in participant_requirements_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Opponent agent {opponent['name']}:{opponent['agent_id']} does not match participant requirements"
                )
            
            # Validate opponent agent exists
            opponent_agent = agent_repo.get_agent(opponent['agent_id'])
            if not opponent_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Opponent agent {opponent['name']} with ID {opponent['agent_id']} not found"
                )
            
            participant_ids.append(opponent['agent_id'])
        
        # Validate required participants are present
        for p_req in participant_requirements:
            if p_req.get('required', True) and not any(p['name'] == p_req['name'] for p in opponents):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Required participant {p_req['name']} not found in opponents"
                )
        
        # Create battle record for database (using participant_ids format for compatibility)
        battle_db_data = {
            'battle_id': str(uuid.uuid4()),
            'green_agent_id': green_agent_id,
            'participant_ids': participant_ids,
            'state': 'pending',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'user_id': battle_data.get('created_by', 'N/A'),
            'interact_history': [],
            'result': None,
            'error': None
        }
        
        # Save to database
        created_battle = battle_repo.create_battle(battle_db_data)
        
        # Add to battle manager queue
        queue_position = battle_manager.add_battle(created_battle['battle_id'], {
            'green_agent_id': green_agent_id,
            'opponents': opponents,
            'config': battle_data.get('config', {})
        })
        
        # Convert to response format (using opponents format for frontend)
        response_data = {
            'battle_id': created_battle['battle_id'],
            'green_agent_id': green_agent_id,
            'opponents': opponents,
            'user_id': created_battle['user_id'],
            'created_at': created_battle['created_at'],
            'state': created_battle['state'],
            'interact_history': created_battle['interact_history'],
            'finished_at': created_battle.get('finished_at'),
            'result': created_battle['result'],
            'error': created_battle['error'],
            'queue_position': queue_position
        }
        
        return BattleResponse(**response_data)
    
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
    battle_id: str = Path(..., description="Battle ID")
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
