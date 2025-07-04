# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

server = FastMCP(
    "Open MCP for AgentBeast Battle Arena",
    host="0.0.0.0",
    port=11000,
)

SESSIONS: dict[str, dict[str, str]] = {}


@server.tool()
def update_battle_result(battle_id: str, info: str) -> None:
    """Log battle status to console and <battle_id>.log."""
    logger.info("Battle %s: %s", battle_id, info)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[INFO] [{timestamp}] {info}\n"
    with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
        f.write(line)


if __name__ == "__main__":
    server.run(transport="sse", log_level="ERROR")
