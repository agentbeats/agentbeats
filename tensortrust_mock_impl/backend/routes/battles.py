import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
import time
import threading
from datetime import datetime
import json
import logging

from ..db.storage import db
from ..a2a_client import a2a_client

router = APIRouter()

battle_queue = []
queue_lock = threading.Lock()
processor_running = False

<<<<<<< HEAD
# LIVE_WS_CHANGE: Global dict to track log subscribers per battle
log_subscribers = {}

# LIVE_WS_CHANGE: WebSocket clients for /ws/battles
battles_ws_clients = set()

logger = logging.getLogger("battles_ws")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# LIVE_WS_CHANGE: Threadsafe broadcast fix
MAIN_EVENT_LOOP = asyncio.get_event_loop()

# LIVE_WS_CHANGE: Broadcast all battles to /ws/battles clients
def broadcast_battles_update():
    """Send the full battles list to all connected /ws/battles clients."""
    try:
        battles = db.list("battles")
        msg = json.dumps({"type": "battles_update", "battles": battles})
        logger.info(f"[battles_ws] Broadcasting battles update to {len(battles_ws_clients)} clients")
        for ws in list(battles_ws_clients):
            try:
                # LIVE_WS_CHANGE: Threadsafe broadcast fix
                asyncio.run_coroutine_threadsafe(ws.send_text(msg), MAIN_EVENT_LOOP)
            except Exception as e:
                logger.warning(f"[battles_ws] Failed to send to client: {e}")
                try:
                    battles_ws_clients.remove(ws)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"[battles_ws] Error in broadcast_battles_update: {e}")

# LIVE_WS_CHANGE: Broadcast a single battle update to /ws/battles clients
def broadcast_battle_update(battle):
    """Send a single battle update to all connected /ws/battles clients."""
    try:
        msg = json.dumps({"type": "battle_update", "battle": battle})
        logger.info(f"[battles_ws] Broadcasting single battle update to {len(battles_ws_clients)} clients")
        for ws in list(battles_ws_clients):
            try:
                # LIVE_WS_CHANGE: Threadsafe broadcast fix
                asyncio.run_coroutine_threadsafe(ws.send_text(msg), MAIN_EVENT_LOOP)
            except Exception as e:
                logger.warning(f"[battles_ws] Failed to send to client: {e}")
                try:
                    battles_ws_clients.remove(ws)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"[battles_ws] Error in broadcast_battle_update: {e}")

def add_battle_log(battle_id: str, message: str, detail: Dict[str, Any] = None, source: str = "system"):
    """Helper function to add a log entry to a battle and push to WebSocket subscribers."""
=======
def add_system_log(battle_id: str, message: str, detail: Dict[str, Any] = None):
    """Helper function to add a log entry to a battle."""
>>>>>>> 30b1e56f0dc8c60e319288214718b71540763ef8
    try:
        log_dict = db.read("system", battle_id)
        if not log_dict:
            return False
<<<<<<< HEAD
        if "logs" not in battle:
            battle["logs"] = []
=======
            
        if "logs" not in log_dict:
            log_dict["logs"] = []
            
>>>>>>> 30b1e56f0dc8c60e319288214718b71540763ef8
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
        }
        if detail:
            log_entry["detail"] = detail
<<<<<<< HEAD
        battle["logs"].append(log_entry)
        db.update("battles", battle_id, battle)
        # Push to WebSocket subscribers
        try:
            import asyncio
            for ws in log_subscribers.get(battle_id, []):
                try:
                    asyncio.create_task(ws.send_json(log_entry))
                except Exception:
                    pass
        except Exception:
            pass
=======
            
        log_dict["logs"].append(log_entry)
        db.update("system", battle_id, log_dict)
>>>>>>> 30b1e56f0dc8c60e319288214718b71540763ef8
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
    for agent_id in [battle["green_agent_id"]] + battle["opponents"]:
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
            # LIVE_WS_CHANGE: Real-time broadcast after finish/error
            broadcast_battle_update(battle)
            return
            
        # Get opponent agents
        opponents = []
        for opponent_id in battle["opponents"]:
            opponent = db.read("agents", opponent_id)
            if not opponent:
                battle = db.read("battles", battle_id)
                battle["state"] = "error"
                battle["error"] = f"Opponent agent {opponent_id} not found"
                db.update("battles", battle_id, battle)
                # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                broadcast_battle_update(battle)
                return
            opponents.append(opponent)

        # Lock the agents
        for agent_id in [battle["green_agent_id"]] + battle["opponents"]:
            agent = db.read("agents", agent_id)
            if agent:
                agent["status"] = "locked"
                db.update("agents", agent_id, agent)
        add_system_log(battle_id, "Agents locked")

        # Reset the agents
        green_launcher = green_agent["register_info"]["launcher_url"]
        blue_launcher = opponents[0]["register_info"]["launcher_url"]
        red_launcher = opponents[1]["register_info"]["launcher_url"] if len(opponents) > 1 else None
        
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
            # LIVE_WS_CHANGE: Real-time broadcast after finish/error
            broadcast_battle_update(battle)
            return
        
        blue_reset = await a2a_client.reset_agent_trigger(
            blue_launcher,
            agent_id=battle["opponents"][0], 
            extra_args={}
        )
        if not blue_reset:
            battle = db.read("battles", battle_id)
            battle["state"] = "error"
            battle["error"] = "Failed to reset blue agent"
            db.update("battles", battle_id, battle)
            add_system_log(battle_id, "Blue agent reset failed")
            unlock_and_unready_agents(battle)
            # LIVE_WS_CHANGE: Real-time broadcast after finish/error
            broadcast_battle_update(battle)
            return        
        
        if red_launcher:
            red_reset = await a2a_client.reset_agent_trigger(
                red_launcher, 
                agent_id=battle["opponents"][1], 
                extra_args={}
            )
            if not red_reset:
                battle = db.read("battles", battle_id)
                battle["state"] = "error"
                battle["error"] = "Failed to reset red agent"
                db.update("battles", battle_id, battle)
                add_system_log(battle_id, "Red agent reset failed")
                unlock_and_unready_agents(battle)
                # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                broadcast_battle_update(battle)
                return

        ready_timeout = battle.get("config", {}).get("ready_timeout", 300)
        agent_ids = [battle["green_agent_id"]] + battle["opponents"]
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
            # LIVE_WS_CHANGE: Real-time broadcast after finish/error
            broadcast_battle_update(battle)
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
            # LIVE_WS_CHANGE: Real-time broadcast after finish/error
            broadcast_battle_update(battle)
            return
        
        blue_agent_id: str = battle["opponents"][0]
        red_agent_id: str = battle["opponents"][1] if len(opponents) > 1 else None
        
        blue_agent_url = db.read("agents", blue_agent_id)["register_info"]["agent_url"]
        red_agent_url = db.read("agents", red_agent_id)["register_info"]["agent_url"] if red_agent_id else None

        notify_success = await a2a_client.notify_green_agent(
            green_agent_url,
            blue_agent_url,
            red_agent_url,
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
            # LIVE_WS_CHANGE: Real-time broadcast after finish/error
            broadcast_battle_update(battle)
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
            # LIVE_WS_CHANGE: Real-time broadcast after finish/error
            broadcast_battle_update(battle)
        
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
        # LIVE_WS_CHANGE: Real-time broadcast after finish
        broadcast_battle_update(battle)

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
        for opponent_id in battle_request['opponents']:
            opponent = db.read("agents", opponent_id)
            if not opponent:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Opponent agent with ID {opponent_id} not found"
                )
                  # Create battle record
        battle_record = {
            "green_agent_id": battle_request['green_agent_id'],
            "opponents": battle_request['opponents'],
            "config": battle_request.get('config', {}),
            "state": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "interact_history": []
        }

        created_battle = db.create("battles", battle_record)
        
        system_log = {
            "logs": [],
            "id": created_battle['id']
        }
        created_system_log = db.create("system", system_log)
        
        with queue_lock:
            battle_queue.append(created_battle['id'])
            created_battle["state"] = "queued"
            db.update("battles", created_battle['id'], created_battle)
            
        # Ensure processor is running
        start_battle_processor()
        # LIVE_WS_CHANGE: Broadcast update
        broadcast_battles_update()
        
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
                "score": event.get("score", {}),
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
        # Broadcast update
        broadcast_battle_update(battle)
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating battle event: {str(e)}")

@router.websocket("/ws/battles/{battle_id}/logs")
async def battle_logs_ws(websocket: WebSocket, battle_id: str):
    logger.info(f"[logs_ws] Client connecting for battle {battle_id}")
    await websocket.accept()
    if battle_id not in log_subscribers:
        log_subscribers[battle_id] = []
    log_subscribers[battle_id].append(websocket)
    try:
        battle = db.read("battles", battle_id)
        if battle and "logs" in battle:
            for log in battle["logs"]:
                await websocket.send_json(log)
        logger.info(f"[logs_ws] Client connected for battle {battle_id}")
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info(f"[logs_ws] Client disconnected for battle {battle_id}")
        log_subscribers[battle_id].remove(websocket)
    except Exception as e:
        logger.warning(f"[logs_ws] Exception for battle {battle_id}: {e}")
        log_subscribers[battle_id].remove(websocket)

@router.websocket("/ws/battles")
async def battles_ws(websocket: WebSocket):
    logger.info("[battles_ws] Client connecting")
    await websocket.accept()
    battles_ws_clients.add(websocket)
    try:
        battles = db.list("battles")
        await websocket.send_text(json.dumps({"type": "battles_update", "battles": battles}))
        logger.info(f"[battles_ws] Client connected. Total clients: {len(battles_ws_clients)}")
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("[battles_ws] Client disconnected")
        battles_ws_clients.remove(websocket)
    except Exception as e:
        logger.warning(f"[battles_ws] Exception: {e}")
        battles_ws_clients.remove(websocket)
