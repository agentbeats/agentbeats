# -*- coding: utf-8 -*-
"""
Battle Royale Green Agent
This agent monitors the battle royale and determines the winner
by checking web services every second for 60 seconds.
"""

import argparse
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from agent_executor import GreenAgentExecutor


SERVER_BASE_URL = "http://localhost"


def build_app(listen_port: int, mcp_url: str) -> A2AStarletteApplication:
    reset_skill = AgentSkill(
        id="green_reset",
        name="Green Resetter",
        description="Reset green agent state to initial state.",
        tags=["reset", "a2a"],
        examples=["reset", "reset your server", "reset the agent"],
    )

    monitor_services_skill = AgentSkill(
        id="green_monitor_services",
        name="Monitor Web Services",
        description="Monitor all agents' web services for 60 seconds.",
        tags=["monitor", "services", "battle"],
        examples=[
            "Monitor all web services",
            "Start monitoring the battle",
        ],
    )

    calculate_scores_skill = AgentSkill(
        id="green_calculate_scores",
        name="Calculate Scores",
        description="Calculate uptime percentages for all agents.",
        tags=["calculate", "scores", "judge"],
        examples=[
            "Calculate agent scores",
            "Determine uptime percentages",
        ],
    )

    determine_winner_skill = AgentSkill(
        id="green_determine_winner",
        name="Determine Winner",
        description="Determine the winner based on uptime percentages.",
        tags=["winner", "judge", "battle"],
        examples=[
            "Determine the winner",
            "Announce the battle results",
        ],
    )

    agent_card = AgentCard(
        name="Battle Royale Green Agent",
        description="A2A green agent that monitors and judges the battle royale competition.",
        url=f"{SERVER_BASE_URL}:{listen_port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[reset_skill, monitor_services_skill, calculate_scores_skill, determine_winner_skill],
        supportsAuthenticatedExtendedCard=False,
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=GreenAgentExecutor(mcp_url=mcp_url),
            task_store=InMemoryTaskStore(),
        ),
    )

    return app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Battle Royale Green Agent server with a configurable port.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="TCP port for the HTTP server to listen on",
        default=9031,
    )
    parser.add_argument(
        "--mcp-url",
        type=str,
        required=True, 
        default="http://localhost:9001/sse",
        help="URL for the MCP server (example: http://localhost:9001/sse)",
    )

    args = parser.parse_args()

    application = build_app(args.port, args.mcp_url)

    uvicorn.run(application.build(), host="0.0.0.0", port=args.port, log_level="debug")


if __name__ == "__main__":
    main() 