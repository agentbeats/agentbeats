# -*- coding: utf-8 -*-
"""
Battle management for AgentBeats backend.
"""

import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
import time
import threading
from datetime import datetime
import os
import logging
import re
import subprocess

from ..db.storage import db
from ..a2a_client import a2a_client
from .websockets import websocket_manager

router = APIRouter()

# Configuration constants
default_ready_timeout = 120
default_battle_timeout = 300

# Global state management
battle_queue = []
queue_lock = threading.Lock()
processor_running = False

logger = logging.getLogger("battles")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# Logging utilities
def add_system_log(
    battle_id: str, message: str, detail: Optional[Dict[str, Any]] = None
):
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
        asyncio.create_task(websocket_manager.broadcast_battle_update(battle))

        return True
    except Exception as e:
        logger.error(f"Error adding system log: {e}")
        return False


# Battle queue processing
def cleanup_stuck_agents():
    """Clean up any agents that are stuck in 'locked' status from previous runs."""
    try:
        agents = db.list("agents")
        unlocked_count = 0
        for agent in agents:
            if agent.get("status") == "locked":
                agent_id = agent.get("agent_id")
                if agent_id and unlock_agent(agent_id):
                    unlocked_count += 1
                    print(
                        f"Unlocked stuck agent: {agent.get('register_info', {}).get('alias', agent_id)}"
                    )

        if unlocked_count > 0:
            print(f"Cleaned up {unlocked_count} stuck agents on startup")
        else:
            print("No stuck agents found on startup")
    except Exception as e:
        print(f"Error cleaning up stuck agents: {str(e)}")


def start_battle_processor():
    """Start the background battle queue processor if not already running."""
    global processor_running
    if processor_running:
        return

    # Clean up any stuck agents on startup
    cleanup_stuck_agents()

    processor_running = True

    # Start the battle queue processing in a background thread
    def process_battle_queue():
        """Background thread that continuously processes battles from the queue."""
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

    threading.Thread(target=process_battle_queue, daemon=True).start()


# Agent management utilities
def unlock_agent(agent_id: str):
    """Unlock a single agent and set it to not ready."""
    agent = db.read("agents", agent_id)
    if agent:
        agent["status"] = "unlocked"
        agent["ready"] = False
        db.update("agents", agent_id, agent)
        return True
    return False


def unlock_and_unready_agents(battle: Dict[str, Any]):
    """Unlock all agents in a battle and set them to not ready."""
    opponent_ids = [op["agent_id"] for op in battle["opponents"]]
    for agent_id in [battle["green_agent_id"]] + opponent_ids:
        unlock_agent(agent_id)


# Battle orchestration
async def process_battle(battle_id: str):
    """Main battle orchestration function - handles the entire battle lifecycle."""

    try:
        # Battle initialization
        battle = db.read("battles", battle_id)
        if not battle:
            print(f"Battle {battle_id} not found")
            return

        battle["state"] = "running"
        db.update("battles", battle_id, battle)
        add_system_log(battle_id, "Battle started")

        # Agent validation
        green_agent = db.read("agents", battle["green_agent_id"])
        if not green_agent:
            battle = db.read("battles", battle_id)
            if battle:
                battle["state"] = "error"
                battle["error"] = "Green agent not found"
                db.update("battles", battle_id, battle)
                update_agent_error_stats(battle)
                unlock_and_unready_agents(battle)
                asyncio.create_task(
                    websocket_manager.broadcast_battle_update(battle)
                )
            return

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
                    update_agent_error_stats(battle)
                    unlock_and_unready_agents(battle)
                    asyncio.create_task(
                        websocket_manager.broadcast_battle_update(battle)
                    )
                return
            opponent_ids.append(opponent_id)

        # Agent locking
        for agent_id in [battle["green_agent_id"]] + opponent_ids:
            agent = db.read("agents", agent_id)
            if agent:
                agent["status"] = "locked"
                db.update("agents", agent_id, agent)
        add_system_log(battle_id, "Agents locked")

        # Agent reset
        green_launcher = green_agent["register_info"]["launcher_url"]
        green_reset = await a2a_client.reset_agent_trigger(
            green_launcher,
            agent_id=battle["green_agent_id"],
            backend_url=os.getenv("PUBLIC_BACKEND_URL"),
            extra_args={},
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
                asyncio.create_task(
                    websocket_manager.broadcast_battle_update(battle)
                )
            return

        opponent_info_send_to_green = []
        for idx, op_id in enumerate(opponent_ids):
            op = db.read("agents", op_id)
            if not op:
                continue
            op_launcher = op["register_info"].get("launcher_url")
            op_reset = await a2a_client.reset_agent_trigger(
                op_launcher,
                agent_id=op_id,
                backend_url=os.getenv("PUBLIC_BACKEND_URL"),
                extra_args={},
            )
            if not op_reset:
                battle = db.read("battles", battle_id)
                if battle:
                    battle["state"] = "error"
                    battle["error"] = (
                        f"Failed to reset {battle['opponents'][idx].get('name')}: {op_id}"
                    )
                    db.update("battles", battle_id, battle)
                    add_system_log(
                        battle_id,
                        f"{battle['opponents'][idx].get('name')} reset failed",
                        {
                            "opponent_id": op_id,
                            "opponent_name": battle["opponents"][idx].get(
                                "name"
                            ),
                        },
                    )
                    update_agent_error_stats(battle)
                    unlock_and_unready_agents(battle)
                    asyncio.create_task(
                        websocket_manager.broadcast_battle_update(battle)
                    )
                return

            # Get the actual agent name from the database, fallback to original name from battle
            original_name = battle["opponents"][idx].get("name", "red_agent")
            agent_name = op.get("register_info", {}).get(
                "alias", original_name
            )
            agent_url = op["register_info"].get("agent_url")

            opponent_info_send_to_green.append(
                {"name": agent_name, "agent_url": agent_url}
            )

        # Agent readiness check
        ready_timeout = default_ready_timeout
        agent_ids = [battle["green_agent_id"]] + opponent_ids
        add_system_log(
            battle_id,
            "Waiting for agents to be ready",
            {"ready_timeout": ready_timeout},
        )

        start_time = time.time()
        while time.time() - start_time < ready_timeout:
            all_ready = True
            for agent_id in agent_ids:
                agent = db.read("agents", agent_id)
                if not agent or not agent.get("ready", False):
                    all_ready = False
                    break
            if all_ready:
                break
            await asyncio.sleep(5)

        if not all_ready:
            battle = db.read("battles", battle_id)
            if battle:
                battle["state"] = "error"
                battle["error"] = (
                    f"Not all agents ready after {ready_timeout} seconds"
                )
                db.update("battles", battle_id, battle)
                add_system_log(
                    battle_id,
                    "Agents not ready timeout",
                    {"ready_timeout": ready_timeout},
                )
                update_agent_error_stats(battle)
                unlock_and_unready_agents(battle)
                asyncio.create_task(
                    websocket_manager.broadcast_battle_update(battle)
                )
            return
        add_system_log(battle_id, "All agents ready", {"agent_ids": agent_ids})

        # Battle execution
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
                asyncio.create_task(
                    websocket_manager.broadcast_battle_update(battle)
                )
            return

        agents_info = {}
        agents_info["green_agent"] = {
            "agent_id": battle["green_agent_id"],
            "agent_url": green_agent_url,
            "agent_name": "green_agent",
        }

        for idx, op_info in enumerate(opponent_info_send_to_green):
            op_id = opponent_ids[idx]
            op_name = battle["opponents"][idx].get("name", "no_name")
            agents_info[op_info["name"]] = {
                "agent_id": op_id,
                "agent_url": op_info["agent_url"],
                "agent_name": op_name,
            }

        for name, agent_info in agents_info.items():
            success = await a2a_client.send_battle_info(
                endpoint=agent_info["agent_url"],
                battle_id=battle_id,
                agent_name=agent_info["agent_name"],
                agent_id=agent_info["agent_id"],
                backend_url=os.getenv("PUBLIC_BACKEND_URL"),
            )
            if not success:
                battle = db.read("battles", battle_id)
                if battle:
                    battle["state"] = "error"
                    battle["error"] = f"Agent {name} failed to respond"
                    db.update("battles", battle_id, battle)
                    add_system_log(
                        battle_id,
                        f"Failed to notify {name} agent",
                        {
                            "agent_name": name,
                            "agent_id": agent_info["agent_id"],
                        },
                    )
                    update_agent_error_stats(battle)
                    unlock_and_unready_agents(battle)
                    asyncio.create_task(
                        websocket_manager.broadcast_battle_update(battle)
                    )
                return

        # Timeout setup
        battle_timeout = green_agent["register_info"].get(
            "battle_timeout", default_battle_timeout
        )
        timeout_thread = threading.Thread(
            target=check_battle_timeout,
            args=(battle_id, battle_timeout),
            daemon=True,
        )
        timeout_thread.start()
        add_system_log(
            battle_id,
            f"Battle timeout set to {battle_timeout} seconds, starting battle.",
        )

        # Query actual agent names from database for logging
        green_agent_name = green_agent.get("register_info", {}).get(
            "alias", "green_agent"
        )

        # Get task description from green agent
        task_config = green_agent.get("register_info", {}).get(
            "task_config", ""
        )

        # Get actual agent names for red agents
        red_agent_names = {}
        for opponent_info in battle["opponents"]:
            opponent_id = opponent_info["agent_id"]
            opponent = db.read("agents", opponent_id)
            if opponent:
                agent_name = opponent.get("register_info", {}).get(
                    "alias", opponent_info.get("name", "red_agent")
                )
                agent_url = opponent.get("register_info", {}).get("agent_url")
                if agent_url:
                    red_agent_names[agent_url] = agent_name

        notify_success = await a2a_client.notify_green_agent(
            green_agent_url,
            opponent_info_send_to_green,
            battle_id,
            backend_url=os.getenv("PUBLIC_BACKEND_URL"),
            green_agent_name=green_agent_name,
            red_agent_names=red_agent_names,
            task_config=task_config,
        )

        if not notify_success:
            battle = db.read("battles", battle_id)
            if battle:
                battle["state"] = "error"
                battle["error"] = "Failed to notify green agent"
                db.update("battles", battle_id, battle)
                add_system_log(
                    battle_id,
                    "Failed to notify green agent",
                    {"green_agent_url": green_agent_url},
                )
                update_agent_error_stats(battle)
                unlock_and_unready_agents(battle)
                asyncio.create_task(
                    websocket_manager.broadcast_battle_update(battle)
                )
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
            asyncio.create_task(
                websocket_manager.broadcast_battle_update(battle)
            )


def check_battle_timeout(battle_id: str, timeout: int):
    """Check if a battle has timed out."""
    time.sleep(timeout)

    battle = db.read("battles", battle_id)
    if battle and battle["state"] == "running":
        add_system_log(
            battle_id, "Battle timed out", {"battle_timeout": timeout}
        )
        battle = db.read("battles", battle_id)
        if battle:
            battle["state"] = "finished"
            battle["result"] = {
                "is_result": True,
                "winner": "draw",
                "score": {"reason": "timeout"},
                "detail": {"message": "Battle timed out"},
                "reported_at": datetime.utcnow().isoformat() + "Z",
            }
            db.update("battles", battle_id, battle)

            update_agent_elos(battle, "draw")

            unlock_and_unready_agents(battle)
            asyncio.create_task(
                websocket_manager.broadcast_battle_update(battle)
            )


# Statistics and ELO management
def update_agent_error_stats(battle: Dict[str, Any]):
    """
    Update error statistics for all agents in a battle that ended in error.
    Increments the error count for all participating agents.
    """
    try:
        agent_ids = [battle["green_agent_id"]] + [
            op["agent_id"] for op in battle["opponents"]
        ]
        for agent_id in agent_ids:
            agent = db.read("agents", agent_id)
            if not agent:
                continue

            if "elo" not in agent:
                agent["elo"] = {
                    "rating": (
                        None
                        if agent.get("register_info", {}).get(
                            "is_green", False
                        )
                        else 1000
                    ),
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
                        "error_rate": 0.0,
                    },
                }

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
                    "error_rate": 0.0,
                }

            stats = agent["elo"]["stats"]
            stats["total_battles"] += 1
            stats["errors"] += 1

            battle_result = {
                "battle_id": battle["battle_id"],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "result": "error",
                "elo_change": 0,
                "final_rating": agent["elo"].get("rating"),
                "opponents": [op["agent_id"] for op in battle["opponents"]],
                "green_agent_id": battle["green_agent_id"],
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
                all_ids = [battle.get("green_agent_id")] + [
                    op.get("agent_id") for op in battle.get("opponents", [])
                ]
                if winner in all_ids:
                    winner_agent_id = winner
        if not winner_agent_id:
            agent_ids = [battle["green_agent_id"]] + [
                op["agent_id"] for op in battle["opponents"]
            ]
            for agent_id in agent_ids:
                agent = db.read("agents", agent_id)
                if not agent:
                    continue
                alias = agent.get("register_info", {}).get("alias")
                card_name = agent.get("agent_card", {}).get("name")
                if winner == alias or winner == card_name:
                    winner_agent_id = agent_id
                    break
        agent_ids = [battle["green_agent_id"]] + [
            op["agent_id"] for op in battle["opponents"]
        ]
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
                        "error_rate": 0.0,
                    },
                }

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
                    "error_rate": 0.0,
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

            stats = agent["elo"]["stats"]
            stats["total_battles"] += 1

            if result == "win":
                stats["wins"] += 1
            elif result == "loss":
                stats["losses"] += 1
            elif result == "draw":
                stats["draws"] += 1

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
                "green_agent_id": battle["green_agent_id"],
            }
            agent["elo"]["battle_history"].append(battle_result)
            db.update("agents", agent_id, agent)
    except Exception as e:
        logging.error(f"Error updating ELO ratings: {e}")


# FastAPI route handlers
@router.get("/battles")
def list_battles() -> List[Dict[str, Any]]:
    """List all battles."""
    try:
        battles = db.list("battles")

        with queue_lock:
            for i, battle_id in enumerate(battle_queue):
                for battle in battles:
                    if battle["battle_id"] == battle_id:
                        battle["queue_position"] = i + 1

        return battles
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing battles: {str(e)}"
        )


@router.get("/battles/{battle_id}")
def get_battle(battle_id: str) -> Dict[str, Any]:
    """Get a single battle by ID."""
    try:
        battle = db.read("battles", battle_id)
        if not battle:
            raise HTTPException(
                status_code=404, detail=f"Battle with ID {battle_id} not found"
            )

        if battle["state"] == "queued":
            with queue_lock:
                if battle_id in battle_queue:
                    battle["queue_position"] = (
                        battle_queue.index(battle_id) + 1
                    )

        return battle
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving battle: {str(e)}"
        )


@router.post("/battles", status_code=status.HTTP_201_CREATED)
def create_battle(battle_request: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new battle."""
    try:
        # Input validation
        if (
            "green_agent_id" not in battle_request
            or "opponents" not in battle_request
        ):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: green_agent_id and opponents",
            )

        green_agent = db.read("agents", battle_request["green_agent_id"])
        if not green_agent:
            raise HTTPException(
                status_code=404,
                detail=f"Green agent with ID {battle_request['green_agent_id']} not found",
            )
        if green_agent.get("status") != "unlocked":
            raise HTTPException(
                status_code=400,
                detail=f"Green agent {green_agent['agent_id']} is not unlocked",
            )

        participant_requirements = green_agent.get("register_info", {}).get(
            "participant_requirements", []
        )
        participant_requirements_names = [
            p["name"] for p in participant_requirements
        ]
        participants = battle_request.get("opponents", [])
        if not isinstance(participants, list):
            raise HTTPException(
                status_code=400, detail="Opponents must be a list"
            )
        for p in participants:
            if (
                not isinstance(p, dict)
                and "name" not in p
                or "agent_id" not in p
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Each opponent must be a dictionary with 'name' and 'agent_id'",
                )
            if p["name"] not in participant_requirements_names:
                raise HTTPException(
                    status_code=400,
                    detail=f"Opponent agent {p['name']}:{p['agent_id']} does not in participant requirements",
                )

            opponent_agent = db.read("agents", p["agent_id"])
            if not opponent_agent:
                raise HTTPException(
                    status_code=404,
                    detail=f"Opponent agent {p['name']} with ID {p['agent_id']} not found",
                )

            if opponent_agent.get("status") != "unlocked":
                raise HTTPException(
                    status_code=400,
                    detail=f"Opponent agent {p['name']} with ID {p['agent_id']} is not unlocked",
                )

        for p_req in participant_requirements:
            if p_req["required"] and not any(
                p["name"] == p_req["name"] for p in participants
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Required participant {p_req['name']} not found in opponents",
                )

        # Battle creation
        battle_record = {
            "green_agent_id": battle_request["green_agent_id"],
            "opponents": battle_request["opponents"],
            "config": battle_request.get("config", {}),
            "state": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "created_by": battle_request.get("created_by", "N/A"),
            "interact_history": [],
        }

        created_system_log = db.create(
            "system", {"logs": [], "battle_id": None}
        )

        battle_record["system_log_id"] = created_system_log["system_log_id"]
        created_battle = db.create("battles", battle_record)

        created_system_log["battle_id"] = created_battle["battle_id"]
        db.update(
            "system", created_system_log["system_log_id"], created_system_log
        )

        # Queue management
        with queue_lock:
            battle_queue.append(created_battle["battle_id"])
            created_battle["state"] = "queued"
            db.update("battles", created_battle["battle_id"], created_battle)

        start_battle_processor()
        try:
            asyncio.run(websocket_manager.broadcast_battles_update())
        except RuntimeError:
            # Event loop already running, skip broadcast
            pass

        return created_battle
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating battle: {str(e)}"
        )


@router.post("/battles/{battle_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_battle_event(battle_id: str, event: Dict[str, Any]):
    """Handle battle result or log entry."""
    try:
        battle = db.read("battles", battle_id)
        if not battle:
            raise HTTPException(
                status_code=404, detail=f"Battle with ID {battle_id} not found"
            )

        battle_state = battle.get("state", "finished")
        if battle_state == "finished":
            raise HTTPException(
                status_code=400,
                detail=f"Battle {battle_id} is not in a valid state for updates: {battle_state}",
            )

        is_result = event.get("is_result", None)
        if is_result is None:
            raise HTTPException(
                status_code=400, detail="Missing is_result field"
            )

        if is_result:
            battle["interact_history"].append(event)

            winner = event.get("winner", "draw")
            update_agent_elos(battle, winner)

            battle["result"] = {
                "winner": winner,
                "detail": event.get("detail", {}),
                "finish_time": event.get(
                    "timestamp", datetime.utcnow().isoformat() + "Z"
                ),
            }
            battle["state"] = "finished"
            unlock_and_unready_agents(battle)
        else:
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat() + "Z"
            logger.info(f"Event: {event}")
            battle["interact_history"].append(event)

        db.update("battles", battle_id, battle)
        try:
            asyncio.run(websocket_manager.broadcast_battle_update(battle))
        except RuntimeError:
            # Event loop already running, skip broadcast
            pass
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating battle event: {str(e)}"
        )
