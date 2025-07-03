# -*- coding: utf-8 -*-

from fastmcp import FastMCP

server = FastMCP("Open MCP for AgentBeast Battle Arena")

# In‑memory session store (will add support later; replace with Redis for production)
SESSIONS: dict[str, dict[str, str]] = {}


@server.tool()
def log_battle_status(info: str, battle_id: str) -> None:
    """
    Log the status of the battle between blue and red agents.
    """

    # TODO: change to [POST] backend/battle/battleId instead
    print(f"Battle Status for battle {battle_id}: {info}")

if __name__ == "__main__":
    # Start the MCP server
    server.run(transport="streamable-http", 
               host="0.0.0.0", port=11000, 
               log_level="info")
