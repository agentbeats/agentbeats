# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from fastmcp import FastMCP
import requests

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

server = FastMCP(
    "Open MCP for AgentBeast Battle Arena",
    host="localhost",
    port=9123,
)

SESSIONS: dict[str, dict[str, str]] = {}

BACKEND_URL = "http://nuggets.puppy9.com:9000"

@server.tool()
def echo(message: str) -> str:
    """
    Echo the input message.
    """
    logger.info("Echoing message: %s", message)
    return f"Echo: {message}"

@server.tool()
def update_battle_process(battle_id: str, info: str) -> str:
    """
    Log battle status to backend API and console.
    Info should be a string (e.g. blue agent's system prompt, red agent's attack prompt, evaluation result, etc.).
    """
    logger.info("Battle %s: %s", battle_id, info)

    # Prepare event data for backend API
    event_data = {
        "eventType": "log",
        "message": info,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Call backend API
        response = requests.post(
            f"{BACKEND_URL}/battles/{battle_id}",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully logged to backend for battle %s", battle_id)
            return 'logged to backend'
        else:
            logger.error("Failed to log to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[INFO] [{timestamp}] {info}\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'logged locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when logging to backend for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[INFO] [{timestamp}] {info}\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'logged locally (network error)'

@server.tool()
def report_on_battle_end(battle_id: str, winner: str, score: dict, detail: dict = None) -> str:
    """
    Report the final battle result to backend API. YOU MUST CALL THIS AT THE END OF THE BATTLE.
    
    Args:
        battle_id: The battle ID
        winner: The winner of the battle ("green", "blue", "red", or "draw")
        score: Score information (dict with reason, points, etc.)
        detail: Additional detail information (optional)
    """
    logger.info("Reporting battle result for %s: winner=%s", battle_id, winner)
    
    # Prepare result event data for backend API
    result_data = {
        "eventType": "result",
        "winner": winner,
        "score": score,
        "reportedAt": datetime.utcnow().isoformat()
    }
    
    if detail:
        result_data["detail"] = detail
    
    try:
        # Call backend API
        response = requests.post(
            f"{BACKEND_URL}/battles/{battle_id}",
            json=result_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("Successfully reported battle result to backend for battle %s", battle_id)
            return f'battle result reported: winner={winner}'
        else:
            logger.error("Failed to report battle result to backend for battle %s: %s", battle_id, response.text)
            # Fallback to local file logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = f"[RESULT] [{timestamp}] Winner: {winner}, Score: {score}\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return 'result logged locally (backend failed)'
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error when reporting battle result for battle %s: %s", battle_id, str(e))
        # Fallback to local file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[RESULT] [{timestamp}] Winner: {winner}, Score: {score}\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return 'result logged locally (network error)'


if __name__ == "__main__":
    server.run(transport="sse", log_level="ERROR")
