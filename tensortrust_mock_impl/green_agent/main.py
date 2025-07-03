# -*- coding: utf-8 -*-
"""
An implementation of a green agent that acts as the judge of the blue & red agents
follows the specification in TensorTrust (https://arxiv.org/abs/2311.01011).

This agent hosts the game between the blue and red agents and decides the winner
based on the game rules. It also provides a reset skill that can reset its own
state and the states of the blue and red agents when needed.
"""

import argparse
import uvicorn

from uuid import uuid4
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from agent_executor import GreenAgentExecutor


def build_app(listen_port: int, 
              blue_agent_url: str, 
              red_agent_url: str, 
              battle_id: str, 
              mcp_url: str) -> A2AStarletteApplication:

    reset_skill = AgentSkill(
        id="green_reset",
        name="Green Resetter",
        description="Reset green agent state to initial state.",
        tags=["reset", "a2a"],
        examples=["reset", "reset your server", "reset the agent"],
    )

    host_battle_skill = AgentSkill(
        id="green_host_battle",
        name="Green Host Battle",
        description=(
            "Host a battle between the blue and red agents, where the blue agent is the defender and the red agent is the attacker. The green agent will judge the battle and decide the winner based on the game rules."
        ),
        tags=["host", "battle", "a2a"],
        examples=[
            "Host a battle between the blue and red agents.",
        ],
    )

    agent_card = AgentCard(
        name="Green Agent (Judge)",
        description=(
            "A2A judge that hosts the battle between the blue and red agents, also  decides the winner of the battle based on the game rules."
        ),
        url=f"http://localhost:{listen_port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[reset_skill, host_battle_skill],
        supportsAuthenticatedExtendedCard=False,
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=GreenAgentExecutor(
                blue_agent_url=blue_agent_url,
                red_agent_url=red_agent_url,
                battle_id=battle_id, 
                mcp_url=mcp_url, 
            ),
            task_store=InMemoryTaskStore(),
        ),
    )

    return app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Green Agent (Judge) server with a configurable port.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=10001,
        help="TCP port for the HTTP server to listen on (default: 10001)",
    )
    parser.add_argument(
        "--blue-agent-url",
        type=str,
        required=True,
        help="URL of the Blue Agent server (e.g., http://localhost:8001/)",
    )
    parser.add_argument(
        "--red-agent-url",
        type=str,
        required=True,
        help="URL of the Red Agent server (e.g., http://localhost:9001/)",
    )
    parser.add_argument(
        "--mcp-url",
        type=str,
        required=True,
        help="URL of the Open MCP server for Agent Beast Battle Arena",
    )
    parser.add_argument(
        "--battle-id", 
        type=str,
        required=True,
        help="Unique identifier for the battle between blue and red agents",
    )

    args = parser.parse_args()

    application = build_app(
        args.port, 
        args.blue_agent_url, 
        args.red_agent_url, 
        args.battle_id,
        args.mcp_url
    )

    uvicorn.run(application.build(), host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
