# -*- coding: utf-8 -*-
"""
WebSocket management for AgentBeats backend.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..db.storage import db

router = APIRouter()

logger = logging.getLogger("websockets")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Global state for WebSocket clients
battles_ws_clients: Set[WebSocket] = set()
log_subscribers: Dict[str, list] = {}

# Threadsafe broadcast fix
MAIN_EVENT_LOOP = asyncio.get_event_loop()

class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    @staticmethod
    async def broadcast_battles_update():
        """Send the full battles list to all connected /ws/battles clients."""
        try:
            battles = db.list("battles")
            msg = json.dumps({"type": "battles_update", "battles": battles})
            logger.info(f"[battles_ws] Broadcasting battles update to {len(battles_ws_clients)} clients")
            for ws in list(battles_ws_clients):
                try:
                    asyncio.run_coroutine_threadsafe(ws.send_text(msg), MAIN_EVENT_LOOP)
                except Exception as e:
                    logger.warning(f"[battles_ws] Failed to send to client: {e}")
                    try:
                        battles_ws_clients.remove(ws)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"[battles_ws] Error in broadcast_battles_update: {e}")

    @staticmethod
    async def broadcast_battle_update(battle: Optional[Dict[str, Any]]):
        """Send a single battle update to all connected /ws/battles clients."""
        try:
            if battle is None:
                return
            msg = json.dumps({"type": "battle_update", "battle": battle})
            logger.info(f"[battles_ws] Broadcasting single battle update to {len(battles_ws_clients)} clients")
            for ws in list(battles_ws_clients):
                try:
                    asyncio.run_coroutine_threadsafe(ws.send_text(msg), MAIN_EVENT_LOOP)
                except Exception as e:
                    logger.warning(f"[battles_ws] Failed to send to client: {e}")
                    try:
                        battles_ws_clients.remove(ws)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"[battles_ws] Error in broadcast_battle_update: {e}")

# Create global instance
websocket_manager = WebSocketManager()

@router.websocket("/ws/battles")
async def battles_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time battle updates."""
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

@router.websocket("/ws/battles/{battle_id}/logs")
async def battle_logs_ws(websocket: WebSocket, battle_id: str):
    """WebSocket endpoint for real-time battle log updates."""
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