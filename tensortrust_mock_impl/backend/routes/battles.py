import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
import time
import threading
from datetime import datetime

from ..db.storage import db
from ..a2a_client import a2a_client

router = APIRouter()

battle_queue = []
queue_lock = threading.Lock()
processor_running = False

def start_battle_processor():
    global processor_running
    if processor_running:
        return
        
    processor_running = True
    threading.Thread(target=process_battle_queue, daemon=True).start()
    
def process_battle_queue():
    global processor_running
    try:
        while processor_running:
            # Get the next battle from the queue
            battle_id = None
            with queue_lock:
                if battle_queue:
                    battle_id = battle_queue.pop(0)
                    
            if battle_id:
                # Process the battle
                asyncio.run(process_battle(battle_id))
                
            # Sleep to avoid busy waiting
            time.sleep(1)
    except Exception as e:
        print(f"Error in battle queue processor: {str(e)}")
    finally:
        processor_running = False

async def wait_agents_ready(agent_ids: list, timeout: int = 300, poll_interval: float = 5):
    """
    Poll the database for agent 'ready' status.
    Wait until all agents in agent_ids are ready or timeout (seconds) is reached.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        all_ready = True
        for agent_id in agent_ids:
            agent = db.read("agents", agent_id)
            if not agent or not agent.get("ready", False):
                all_ready = False
                break
        if all_ready:
            return True
        await asyncio.sleep(poll_interval)
    return False

def unlock_and_unready_agents(battle: Dict[str, Any]):
    for agent_id in [battle["greenAgentId"]] + battle["opponents"]:
        agent = db.read("agents", agent_id)
        if agent:
            agent["status"] = "unlocked"
            agent["ready"] = False
            db.update("agents", agent_id, agent)
            
async def process_battle(battle_id: str):
    
    # TODO: call unlock_and_reset_agents too many times...
    try:
        # Get the battle info
        battle = db.read("battles", battle_id)
        if not battle:
            print(f"Battle {battle_id} not found")
            return
            
        # Update battle state to running
        battle["state"] = "running"
        db.update("battles", battle_id, battle)
        
        # Get the green agent info
        green_agent = db.read("agents", battle["greenAgentId"])
        if not green_agent:
            battle["state"] = "error"
            battle["error"] = "Green agent not found"
            db.update("battles", battle_id, battle)
            return
            
        # Get opponent agents
        opponents = []
        for opponent_id in battle["opponents"]:
            opponent = db.read("agents", opponent_id)
            if not opponent:
                battle["state"] = "error"
                battle["error"] = f"Opponent agent {opponent_id} not found"
                db.update("battles", battle_id, battle)
                return
            opponents.append(opponent)
            
        # Lock the agents
        for agent_id in [battle["greenAgentId"]] + battle["opponents"]:
            agent = db.read("agents", agent_id)
            if agent:
                agent["status"] = "locked"
                db.update("agents", agent_id, agent)
                
        # Reset the agents
        green_starter = green_agent["registerInfo"]["starter"]
        blue_starter = opponents[0]["registerInfo"]["starter"]
        red_starter = opponents[1]["registerInfo"]["starter"] if len(opponents) > 1 else None
        
        green_reset = a2a_client.reset_agent_trigger(green_starter)
        if not green_reset:
            battle["state"] = "error"
            battle["error"] = "Failed to reset green agent"
            db.update("battles", battle_id, battle)
            unlock_and_unready_agents(battle)
            return
            
        blue_reset = a2a_client.reset_agent_trigger(blue_starter)
        if not blue_reset:
            battle["state"] = "error"
            battle["error"] = "Failed to reset blue agent"
            db.update("battles", battle_id, battle)
            unlock_and_unready_agents(battle)
            return
            
        if red_starter:
            red_reset = a2a_client.reset_agent_trigger(red_starter)
            if not red_reset:
                battle["state"] = "error"
                battle["error"] = "Failed to reset red agent"
                db.update("battles", battle_id, battle)
                unlock_and_unready_agents(battle)
                return

        # Wait for all agents to be ready
        ready_timeout = battle.get("config", {}).get("readyTimeout", 300)  # default 30 seconds
        agent_ids = [battle["greenAgentId"]] + battle["opponents"]
        ready = await wait_agents_ready(agent_ids, timeout=ready_timeout)
        if not ready:
            battle["state"] = "error"
            battle["error"] = f"Not all agents ready after {ready_timeout} seconds"
            db.update("battles", battle_id, battle)
            unlock_and_unready_agents(battle)
            return
                
        # Kick off the battle by notifying the green agent
        green_endpoint = green_agent["registerInfo"]["endpoint"]
        if not green_endpoint:
            battle["state"] = "error"
            battle["error"] = "Green agent endpoint not found"
            db.update("battles", battle_id, battle)
            unlock_and_unready_agents(battle)
            return
        
        blue_agent_card = opponents[0]["agentCard"]
        red_agent_card = opponents[1]["agentCard"] if len(opponents) > 1 else None
        
        notify_success = await a2a_client.notify_green_agent(
            green_endpoint,
            blue_agent_card,
            red_agent_card,
            battle_id
        )
        
        if not notify_success:
            battle["state"] = "error"
            battle["error"] = "Failed to notify green agent"
            db.update("battles", battle_id, battle)
            unlock_and_unready_agents(battle)
            return

        print(f"Battle {battle_id} kick off successfully with green agent {green_agent['id']} and opponents {[opponent['id'] for opponent in opponents]}")
            
        # Set a timeout for the battle (using a simple approach for now)
        timeout = battle.get("config", {}).get("timeout", 300)  # Default 5 minutes
        timeout_thread = threading.Thread(
            target=check_battle_timeout,
            args=(battle_id, timeout),
            daemon=True
        )
        timeout_thread.start()
        
    except Exception as e:
        print(f"Error processing battle {battle_id}: {str(e)}")
        battle = db.read("battles", battle_id)
        if battle:
            battle["state"] = "error"
            battle["error"] = str(e)
            db.update("battles", battle_id, battle)
            unlock_and_unready_agents(battle)
        
def check_battle_timeout(battle_id: str, timeout: int):
    """Check if a battle has timed out."""
    time.sleep(timeout)
    
    # Check if the battle is still running
    battle = db.read("battles", battle_id)
    if battle and battle["state"] == "running":
        # Battle timed out
        battle["state"] = "finished"
        battle["result"] = {
            "winner": "draw",
            "score": {"reason": "timeout"},
            "detail": {"message": "Battle timed out"},
            "reportedAt": datetime.utcnow().isoformat()
        }
        db.update("battles", battle_id, battle)
        
        unlock_and_unready_agents(battle)

@router.post("/battles", status_code=status.HTTP_201_CREATED)
def create_battle(battle_request: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new battle."""
    try:
        # Validate required fields
        if 'greenAgentId' not in battle_request or 'opponents' not in battle_request:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: greenAgentId and opponents"
            )
            
        # Validate agents
        green_agent = db.read("agents", battle_request['greenAgentId'])
        if not green_agent:
            raise HTTPException(
                status_code=404, 
                detail=f"Green agent with ID {battle_request['greenAgentId']} not found"
            )
        for opponent_id in battle_request['opponents']:
            opponent = db.read("agents", opponent_id)
            if not opponent:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Opponent agent with ID {opponent_id} not found"
                )
                
        # Create battle record
        battle_record = {
            "greenAgentId": battle_request['greenAgentId'],
            "opponents": battle_request['opponents'],
            "config": battle_request.get('config', {}),
            "state": "pending",
            "createdAt": datetime.utcnow().isoformat()
        }
        created_battle = db.create("battles", battle_record)
        
        with queue_lock:
            battle_queue.append(created_battle['id'])
            created_battle["state"] = "queued"
            db.update("battles", created_battle['id'], created_battle)
            
        # Ensure processor is running
        start_battle_processor()
        
        return created_battle
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating battle: {str(e)}")
        
@router.get("/battles")
def list_battles() -> List[Dict[str, Any]]:
    """List all battles."""
    try:
        battles = db.list("battles")
        
        # Add queue position information
        with queue_lock:
            for i, battle_id in enumerate(battle_queue):
                for battle in battles:
                    if battle['id'] == battle_id:
                        battle['queuePosition'] = i + 1
                        
        return battles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing battles: {str(e)}")
        
@router.get("/battles/{battle_id}")
def get_battle(battle_id: str) -> Dict[str, Any]:
    """Get a single battle by ID."""
    try:
        battle = db.read("battles", battle_id)
        if not battle:
            raise HTTPException(status_code=404, detail=f"Battle with ID {battle_id} not found")
            
        # Add queue position information if queued
        if battle["state"] == "queued":
            with queue_lock:
                if battle_id in battle_queue:
                    battle['queuePosition'] = battle_queue.index(battle_id) + 1
                    
        return battle
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving battle: {str(e)}")
        
@router.post("/battles/{battle_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_battle_result(battle_id: str, result: Dict[str, Any]):
    """Update battle result reported by green agent."""
    try:
        battle = db.read("battles", battle_id)
        if not battle:
            raise HTTPException(status_code=404, detail=f"Battle with ID {battle_id} not found")
            
        # Update the battle result
        battle["result"] = result
        battle["state"] = "finished"
        db.update("battles", battle_id, battle)
        
        unlock_and_unready_agents(battle)
                
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating battle result: {str(e)}")
