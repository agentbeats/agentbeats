import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
import time
import threading
from datetime import datetime
import json
import logging
import toml
import os

from ..db.storage import db
from ..a2a_client import a2a_client

router = APIRouter()

# Configuration loading
def load_config():
    """Load configuration from backend_cfg.toml"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "backend_cfg.toml")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}, using defaults")
        return {}

# Load configuration once at module level
CONFIG = load_config()

battle_queue = []
queue_lock = threading.Lock()
processor_running = False

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
def broadcast_battle_update(battle: Optional[Dict[str, Any]]):
    """Send a single battle update to all connected /ws/battles clients."""
    try:
        if battle is None:
            return
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

def add_system_log(battle_id: str, message: str, detail: Optional[Dict[str, Any]] = None):
    """Helper function to add a log entry to a battle and push to WebSocket subscribers."""
    try:
        battle = db.read("battles", battle_id)
        if not battle:
            return False
            
        if "interact_history" not in battle:
            battle["interact_history"] = []
            
        log_entry = {
            "is_result": False,
            "message": message,
            "reported_by": "system",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if detail is not None:
            log_entry["detail"] = detail
        battle["interact_history"].append(log_entry)
        db.update("battles", battle_id, battle)
        
        # Broadcast the updated battle to all subscribers
        broadcast_battle_update(battle)
        
        return True
    except Exception as e:
        logger.error(f"Error adding system log: {e}")
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
            if battle:
                battle["state"] = "error"
                battle["error"] = "Green agent not found"
                db.update("battles", battle_id, battle)
                # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                broadcast_battle_update(battle)
            return
            
        # Get opponent agents
        opponent_ids = []
        for opponent_info in battle["opponents"]:
            opponent_id = opponent_info["agent_id"]
            opponent = db.read("agents", opponent_id)
            if not opponent:
                battle = db.read("battles", battle_id)
                if battle:
                    battle["state"] = "error"
                    battle["error"] = f"Opponent agent {opponent_id} not found"
                    db.update("battles", battle_id, battle)
                    # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                    broadcast_battle_update(battle)
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
            if battle:
                battle["state"] = "error"
                battle["error"] = "Failed to reset green agent"
                db.update("battles", battle_id, battle)
                add_system_log(battle_id, "Green agent reset failed")
                update_agent_error_stats(battle)
                unlock_and_unready_agents(battle)
                # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                broadcast_battle_update(battle)
            return

        # Reset opponent agents and get their URLs
        opponent_info_send_to_green = [{'name': op["name"]} for op in battle["opponents"]]
        for idx, op_id in enumerate(opponent_ids):
            op = db.read("agents", op_id)
            if not op:
                continue
            op_launcher = op["register_info"].get("launcher_url")
            op_reset = await a2a_client.reset_agent_trigger(
                op_launcher, 
                agent_id=op_id, 
                extra_args={}
            )    
            if not op_reset:
                battle = db.read("battles", battle_id)
                if battle:
                    battle["state"] = "error"
                    battle["error"] = f"Failed to reset {battle['opponents'][idx].get('name')}: {op_id}"
                    db.update("battles", battle_id, battle)
                    add_system_log(battle_id, f"{battle['opponents'][idx].get('name')} reset failed", {
                        "opponent_id": op_id,
                        "opponent_name": battle["opponents"][idx].get("name")
                    })
                    update_agent_error_stats(battle)
                    unlock_and_unready_agents(battle)
                    # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                    broadcast_battle_update(battle)
                return

            opponent_info_send_to_green[idx]["agent_url"] = op["register_info"].get("agent_url")
            

        ready_timeout = CONFIG.get("battle", {}).get("ready_timeout", 300) # TODO: Should be configurable
        agent_ids = [battle["green_agent_id"]] + opponent_ids
        add_system_log(battle_id, "Waiting for agents to be ready", {
            "ready_timeout": ready_timeout
        })
        ready = await wait_agents_ready(agent_ids, timeout=ready_timeout)
        
        if not ready:
            battle = db.read("battles", battle_id)
            if battle:
                battle["state"] = "error"
                battle["error"] = f"Not all agents ready after {ready_timeout} seconds"
                db.update("battles", battle_id, battle)
                add_system_log(battle_id, "Agents not ready timeout", {"ready_timeout": ready_timeout})
                update_agent_error_stats(battle)
                unlock_and_unready_agents(battle)
                # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                broadcast_battle_update(battle)
            return
        add_system_log(battle_id, "All agents ready", {"agent_ids": agent_ids})
                
        # Kick off the battle by notifying the green agent
        green_agent_url = green_agent["register_info"]["agent_url"]
        if not green_agent_url:
            battle = db.read("battles", battle_id)
            if battle:
                battle["state"] = "error"
                battle["error"] = "Green agent url not found"
                db.update("battles", battle_id, battle)
                add_system_log(battle_id, "Green agent url not found")
                update_agent_error_stats(battle)
                unlock_and_unready_agents(battle)
                # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                broadcast_battle_update(battle)
            return

        
        
        battle_timeout = green_agent['register_info'].get('battle_timeout', CONFIG.get("battle", {}).get("default_battle_timeout", 300))
        timeout_thread = threading.Thread(
            target=check_battle_timeout,
            args=(battle_id, battle_timeout),
            daemon=True
        )
        timeout_thread.start()
        add_system_log(battle_id, f"Battle timeout set to {battle_timeout} seconds, starting battle.")
        
        notify_success = await a2a_client.notify_green_agent(
            green_agent_url,
            opponent_info_send_to_green,
            battle_id
        )
        
        if not notify_success:
            battle = db.read("battles", battle_id)
            if battle:
                battle["state"] = "error"
                battle["error"] = "Failed to notify green agent"
                db.update("battles", battle_id, battle)
                add_system_log(battle_id, "Failed to notify green agent", {
                    "green_agent_url": green_agent_url
                })
                update_agent_error_stats(battle)
                unlock_and_unready_agents(battle)
                # LIVE_WS_CHANGE: Real-time broadcast after finish/error
                broadcast_battle_update(battle)
            return
            
        
    except Exception as e:
        print(f"Error processing battle {battle_id}: {str(e)}")
        battle = db.read("battles", battle_id)
        if battle:
            battle["state"] = "error"
            battle["error"] = str(e)
            db.update("battles", battle_id, battle)
            update_agent_error_stats(battle)
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
        if battle:
            battle["state"] = "finished"
            battle["result"] = {
                "is_result": True,
                "winner": "draw",
                "score": {"reason": "timeout"},
                "detail": {"message": "Battle timed out"},
                "reported_at": datetime.utcnow().isoformat() + "Z"
            }
            db.update("battles", battle_id, battle)
            
            # Update ELOs for timeout (draw)
            update_agent_elos(battle, "draw")
            
            unlock_and_unready_agents(battle)
            # LIVE_WS_CHANGE: Real-time broadcast after finish
            broadcast_battle_update(battle)

def update_agent_error_stats(battle: Dict[str, Any]):
    """
    Update error statistics for all agents in a battle that ended in error.
    Increments the error count for all participating agents.
    """
    try:
        agent_ids = [battle["green_agent_id"]] + [op["agent_id"] for op in battle["opponents"]]
        for agent_id in agent_ids:
            agent = db.read("agents", agent_id)
            if not agent:
                continue
            
            # Initialize ELO structure if not present
            if "elo" not in agent:
                agent["elo"] = {
                    "rating": None if agent.get("register_info", {}).get("is_green", False) else 1000,
                    "battle_history": [],
                    "stats": {
                        "wins": 0,
                        "losses": 0,
                        "draws": 0,
                        "errors": 0,
                        "total_battles": 0,
                        "win_rate": 0.0,
                        "loss_rate": 0.0,
                        "draw_rate": 0.0,
                        "error_rate": 0.0
                    }
                }
            
            # Initialize stats if not present (for backward compatibility)
            if "stats" not in agent["elo"]:
                agent["elo"]["stats"] = {
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "errors": 0,
                    "total_battles": 0,
                    "win_rate": 0.0,
                    "loss_rate": 0.0,
                    "draw_rate": 0.0,
                    "error_rate": 0.0
                }
            
            # Update error stats
            stats = agent["elo"]["stats"]
            stats["total_battles"] += 1
            stats["errors"] += 1
            

            
            # Add error battle result to history
            battle_result = {
                "battle_id": battle["battle_id"],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "result": "error",
                "elo_change": 0,
                "final_rating": agent["elo"].get("rating"),
                "opponents": [op["agent_id"] for op in battle["opponents"]],
                "green_agent_id": battle["green_agent_id"]
            }
            agent["elo"]["battle_history"].append(battle_result)
            db.update("agents", agent_id, agent)
    except Exception as e:
        logging.error(f"Error updating agent error stats: {e}")

def update_agent_elos(battle: Dict[str, Any], winner: str):
    """
    Update ELO ratings and statistics for all agents in a battle.
    Winner gains 15 ELO, others lose 15 ELO.
    Winner can be an agent_id, a role, or an agent alias/name.
    Green agents never have a rating (set to None or 'N/A'), but keep battle history and stats.
    """
    try:
        # Map winner to agent_id if needed
        winner_agent_id = None
        if winner == "draw":
            winner_agent_id = None
        elif winner == "green_agent":
            winner_agent_id = battle.get("green_agent_id")
        else:
            for op in battle.get("opponents", []):
                if op.get("name") == winner or op.get("role") == winner:
                    winner_agent_id = op.get("agent_id")
                    break
            if not winner_agent_id:
                all_ids = [battle.get("green_agent_id")] + [op.get("agent_id") for op in battle.get("opponents", [])]
                if winner in all_ids:
                    winner_agent_id = winner
        if not winner_agent_id:
            agent_ids = [battle["green_agent_id"]] + [op["agent_id"] for op in battle["opponents"]]
            for agent_id in agent_ids:
                agent = db.read("agents", agent_id)
                if not agent:
                    continue
                alias = agent.get("register_info", {}).get("alias")
                card_name = agent.get("agent_card", {}).get("name")
                if winner == alias or winner == card_name:
                    winner_agent_id = agent_id
                    break
        agent_ids = [battle["green_agent_id"]] + [op["agent_id"] for op in battle["opponents"]]
        for agent_id in agent_ids:
            agent = db.read("agents", agent_id)
            if not agent:
                continue
            is_green = agent.get("register_info", {}).get("is_green", False)
            if "elo" not in agent:
                agent["elo"] = {
                    "rating": None if is_green else 1000,
                    "battle_history": [],
                    "stats": {
                        "wins": 0,
                        "losses": 0,
                        "draws": 0,
                        "errors": 0,
                        "total_battles": 0,
                        "win_rate": 0.0,
                        "loss_rate": 0.0,
                        "draw_rate": 0.0,
                        "error_rate": 0.0
                    }
                }
            
            # Initialize stats if not present (for backward compatibility)
            if "stats" not in agent["elo"]:
                agent["elo"]["stats"] = {
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "errors": 0,
                    "total_battles": 0,
                    "win_rate": 0.0,
                    "loss_rate": 0.0,
                    "draw_rate": 0.0,
                    "error_rate": 0.0
                }
            
            if winner == "draw":
                elo_change = 0
                result = "draw"
            elif agent_id == winner_agent_id:
                elo_change = 15
                result = "win"
            else:
                elo_change = -15
                result = "loss"
            
            # Update stats
            stats = agent["elo"]["stats"]
            stats["total_battles"] += 1
            
            if result == "win":
                stats["wins"] += 1
            elif result == "loss":
                stats["losses"] += 1
            elif result == "draw":
                stats["draws"] += 1
            

            
            # Only update rating for non-green agents
            if not is_green and agent["elo"]["rating"] is not None:
                agent["elo"]["rating"] += elo_change
                final_rating = agent["elo"]["rating"]
            else:
                final_rating = None
            battle_result = {
                "battle_id": battle["battle_id"],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "result": result,
                "elo_change": elo_change,
                "final_rating": final_rating,
                "opponents": [op["agent_id"] for op in battle["opponents"]],
                "green_agent_id": battle["green_agent_id"]
            }
            agent["elo"]["battle_history"].append(battle_result)
            db.update("agents", agent_id, agent)
    except Exception as e:
        logging.error(f"Error updating ELO ratings: {e}")

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
        if not isinstance(participants, list):
            raise HTTPException(
                status_code=400, 
                detail="Opponents must be a list"
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
            if p_req['required'] and not any(p['name'] == p_req['name'] for p in participants):
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
            "created_at": datetime.utcnow().isoformat() + "Z",
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

            # Determine winner and update ELOs
            winner = event.get("winner", "draw")
            update_agent_elos(battle, winner)

            battle["result"] = {
                "winner": winner,
                "detail": event.get("detail", {}),
                "finish_time": event.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            }
            battle["state"] = "finished"
            unlock_and_unready_agents(battle)
        else:
            # timestamp, is_result, message, detail
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
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
        # Get the battle to find the system_log_id
        battle = db.read("battles", battle_id)
        if battle and battle.get("system_log_id"):
            system_log = db.read("system", battle["system_log_id"])
            if system_log and "logs" in system_log:
                # Send existing logs to the client
                for log in system_log["logs"]:
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
