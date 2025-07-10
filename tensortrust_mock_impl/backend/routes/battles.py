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

def add_system_log(battle_id: str, message: str, detail: Dict[str, Any] = None):
    """Helper function to add a log entry to a battle."""
    try:
        battle = db.read("battles", battle_id)
        system_log_id = battle.get("system_log_id")
        log_dict = db.read("system", system_log_id)
        if not log_dict:
            return False
            
        if "logs" not in log_dict:
            log_dict["logs"] = []
            
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
        }
        
        if detail:
            log_entry["detail"] = detail
            
        log_dict["logs"].append(log_entry)
        db.update("system", system_log_id, log_dict)
        return True
        
    except Exception as e:
        print(f"Error adding battle log: {str(e)}")
        return False

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
    opponent_ids = [op["agent_id"] for op in battle["opponents"]]
    for agent_id in [battle["green_agent_id"]] + opponent_ids:
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
        add_system_log(battle_id, "Battle started")
        
        # Get the green agent info
        green_agent = db.read("agents", battle["green_agent_id"])
        if not green_agent:
            battle = db.read("battles", battle_id)
            battle["state"] = "error"
            battle["error"] = "Green agent not found"
            db.update("battles", battle_id, battle)
            return
            
        # Get opponent agents
        opponent_ids = []
        for opponent_info in battle["opponents"]:
            opponent_id = opponent_info["agent_id"]
            opponent = db.read("agents", opponent_id)
            if not opponent:
                battle = db.read("battles", battle_id)
                battle["state"] = "error"
                battle["error"] = f"Opponent agent {opponent_id} not found"
                db.update("battles", battle_id, battle)
                return
            opponent_ids.append(opponent_id)

        # Lock the agents
        for agent_id in [battle["green_agent_id"]] + opponent_ids:
            agent = db.read("agents", agent_id)
            if agent:
                agent["status"] = "locked"
                db.update("agents", agent_id, agent)
        add_system_log(battle_id, "Agents locked")

        # Reset the agents
        green_launcher = green_agent["register_info"]["launcher_url"]        
        green_reset = await a2a_client.reset_agent_trigger(
            green_launcher, 
            agent_id=battle["green_agent_id"], 
            extra_args={"mcp-url": "http://localhost:9001/sse/"}
        )
        if not green_reset:
            battle = db.read("battles", battle_id)
            battle["state"] = "error"
            battle["error"] = "Failed to reset green agent"
            db.update("battles", battle_id, battle)
            add_system_log(battle_id, "Green agent reset failed")
            unlock_and_unready_agents(battle)
            return

        # Reset opponent agents and get their URLs
        opponent_info_send_to_green = [{'name': op["name"]} for op in battle["opponents"]]
        for idx, op_id in enumerate(opponent_ids):
            op = db.read("agents", op_id)
            op_launcher = op["register_info"].get("launcher_url")
            op_reset = await a2a_client.reset_agent_trigger(
                op_launcher, 
                agent_id=op_id, 
            )
            if not op_reset:
                battle = db.read("battles", battle_id)
                battle["state"] = "error"
                battle["error"] = f"Failed to reset {battle['opponents'][idx].get('name')}: {op_id}"
                db.update("battles", battle_id, battle)
                add_system_log(battle_id, f"{battle['opponents'][idx].get('name')} reset failed", {
                    "opponent_id": op_id,
                    "opponent_name": battle["opponents"][idx].get("name")
                })
                unlock_and_unready_agents(battle)
                return

            opponent_info_send_to_green[idx]["agent_url"] = op["register_info"].get("agent_url")
            

        ready_timeout = battle.get("config", {}).get("ready_timeout", 300)
        agent_ids = [battle["green_agent_id"]] + opponent_ids
        add_system_log(battle_id, "Waiting for agents to be ready", {
            "ready_timeout": ready_timeout
        })
        ready = await wait_agents_ready(agent_ids, timeout=ready_timeout)
        
        if not ready:
            battle = db.read("battles", battle_id)
            battle["state"] = "error"
            battle["error"] = f"Not all agents ready after {ready_timeout} seconds"
            db.update("battles", battle_id, battle)
            add_system_log(battle_id, "Agents not ready timeout", {"ready_timeout": ready_timeout})
            unlock_and_unready_agents(battle)
            return
        add_system_log(battle_id, "All agents ready", {"agent_ids": agent_ids})
                
        # Kick off the battle by notifying the green agent
        green_agent_url = green_agent["register_info"]["agent_url"]
        if not green_agent_url:
            battle = db.read("battles", battle_id)
            battle["state"] = "error"
            battle["error"] = "Green agent url not found"
            db.update("battles", battle_id, battle)
            add_system_log(battle_id, "Green agent url not found")
            unlock_and_unready_agents(battle)
            return
        
        notify_success = await a2a_client.notify_green_agent(
            green_agent_url,
            opponent_info_send_to_green,
            battle_id
        )
        
        if not notify_success:
            battle = db.read("battles", battle_id)
            battle["state"] = "error"
            battle["error"] = "Failed to notify green agent"
            db.update("battles", battle_id, battle)
            add_system_log(battle_id, "Failed to notify green agent", {
                "green_agent_url": green_agent_url
            })
            unlock_and_unready_agents(battle)
            return

        add_system_log(battle_id, "Green agent notified, battle commenced")
            
        battle_timeout = battle.get("config", {}).get("battle_timeout", 300)
        timeout_thread = threading.Thread(
            target=check_battle_timeout,
            args=(battle_id, battle_timeout),
            daemon=True
        )
        timeout_thread.start()
        
    except Exception as e:
        print(f"Error processing battle {battle_id}: {str(e)}")
        battle = db.read("battles", battle_id)
        if battle:
            battle = db.read("battles", battle_id)
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
        add_system_log(battle_id, "Battle timed out", {"battle_timeout": timeout})
        battle = db.read("battles", battle_id)
        battle["state"] = "finished"
        battle["result"] = {
            "is_result": True,
            "winner": "draw",
            "score": {"reason": "timeout"},
            "detail": {"message": "Battle timed out"},
            "reported_at": datetime.utcnow().isoformat()
        }
        db.update("battles", battle_id, battle)
        
        unlock_and_unready_agents(battle)

@router.post("/battles", status_code=status.HTTP_201_CREATED)
def create_battle(battle_request: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new battle."""
    try:
        # Validate required fields
        if 'green_agent_id' not in battle_request or 'opponents' not in battle_request:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: green_agent_id and opponents"
            )
            
        # Validate agents
        green_agent = db.read("agents", battle_request['green_agent_id'])
        if not green_agent:
            raise HTTPException(
                status_code=404, 
                detail=f"Green agent with ID {battle_request['green_agent_id']} not found"
            )

        # Validate opponent agents
        participant_requirements = green_agent.get("register_info", {}).get("participant_requirements", [])
        participant_requirements_names = [p['name'] for p in participant_requirements]
        participants = battle_request.get('opponents', [])
        if not isinstance(participants, list) or len(participants) < 1:
            raise HTTPException(
                status_code=400, 
                detail="Opponents must be a list with at least one participant"
            )
        for p in participants:
            if not isinstance(p, dict) and 'name' not in p or 'agent_id' not in p:
                raise HTTPException(
                    status_code=400, 
                    detail="Each opponent must be a dictionary with 'name' and 'agent_id'"
                )
            if p['name'] not in participant_requirements_names:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Opponent agent {p['name']}:{p['agent_id']} does not in participant requirements"
                )

            opponent_agent = db.read("agents", p['agent_id'])
            if not opponent_agent:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Opponent agent {p['name']} with ID {p['agent_id']} not found"
                )

        for p_req in participant_requirements:
            if p_req['required'] and not any(
                p['name'] == p_req['name']
                for p in participants
            ):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Required participant {p_req['name']} not found in opponents"
                )
            
        # Create battle record
        battle_record = {
            "green_agent_id": battle_request['green_agent_id'],
            "opponents": battle_request['opponents'], # list of dicts with 'name' and 'agent_id'
            "config": battle_request.get('config', {}),
            "state": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "interact_history": []
        }

        created_system_log = db.create("system", {"logs": [], "battle_id": None})

        battle_record["system_log_id"] = created_system_log['system_log_id']
        created_battle = db.create("battles", battle_record)
        
        # Update the system log with the battle ID
        created_system_log["battle_id"] = created_battle['battle_id']
        db.update("system", created_system_log['system_log_id'], created_system_log)
        
        with queue_lock:
            battle_queue.append(created_battle['battle_id'])
            created_battle["state"] = "queued"
            db.update("battles", created_battle['battle_id'], created_battle)
            
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
                    if battle['battle_id'] == battle_id:
                        battle['queue_position'] = i + 1
                        
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
                    battle['queue_position'] = battle_queue.index(battle_id) + 1
                    
        return battle
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving battle: {str(e)}")
        
@router.post("/battles/{battle_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_battle_event(battle_id: str, event: Dict[str, Any]):
    """Handle battle result or log entry."""
    try:
        battle = db.read("battles", battle_id)
        if not battle:
            raise HTTPException(status_code=404, detail=f"Battle with ID {battle_id} not found")

        battle_state = battle.get("state", "finished")
        if battle_state == "finished":
            raise HTTPException(
                status_code=400, 
                detail=f"Battle {battle_id} is not in a valid state for updates: {battle_state}"
            )
            
        # Check event type
        is_result = event.get("is_result", None)
        if is_result is None:
            raise HTTPException(status_code=400, detail="Missing is_result field")
            
        if is_result:
            # Update the battle result
            battle["interact_history"].append(event)

            battle["result"] = {
                "winner": event.get("winner", "draw"),
                "detail": event.get("detail", {}),
                "finish_time": event.get("timestamp", datetime.utcnow().isoformat()),
            }
            battle["state"] = "finished"
            unlock_and_unready_agents(battle)
        else:
            # timestamp, is_result, message, detail
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
    
            battle["interact_history"].append(event)

        
        db.update("battles", battle_id, battle)
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating battle event: {str(e)}")
