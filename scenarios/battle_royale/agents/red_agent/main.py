# -*- coding: utf-8 -*-
"""
Battle Royale Red Agent
This agent competes in the battle royale by SSHing into the battle arena
and creating a web service on port 80 serving its own name.
"""

import argparse
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from agent_executor import RedAgentExecutor


SERVER_BASE_URL = "http://localhost"


def build_app(listen_port: int) -> A2AStarletteApplication:
    reset_skill = AgentSkill(
        id="red_reset",
        name="Red Resetter",
        description="Reset red agent state to initial state.",
        tags=["reset", "a2a"],
        examples=["reset", "reset your server", "reset the agent"],
    )

    ssh_connect_skill = AgentSkill(
        id="red_ssh_connect",
        name="SSH Connect",
        description="Connect to the battle arena via SSH using provided credentials.",
        tags=["ssh", "connect", "battle"],
        examples=[
            "Connect to the battle arena via SSH",
            "SSH into the container",
        ],
    )

    create_web_service_skill = AgentSkill(
        id="red_create_web_service",
        name="Create Web Service",
        description="Create a web service on port 80 serving the agent's name.",
        tags=["web", "service", "port80"],
        examples=[
            "Create a web service on port 80",
            "Start a web server serving my name",
        ],
    )

    block_others_skill = AgentSkill(
        id="red_block_others",
        name="Block Other Services",
        description="Attempt to block other agents' web services from running.",
        tags=["block", "compete", "attack"],
        examples=[
            "Block other agents' services",
            "Stop competing web services",
        ],
    )

    agent_card = AgentCard(
        name="Battle Royale Red Agent",
        description="A2A red agent that competes in battle royale by creating web services and blocking competitors.",
        url=f"{SERVER_BASE_URL}:{listen_port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[reset_skill, ssh_connect_skill, create_web_service_skill, block_others_skill],
        supportsAuthenticatedExtendedCard=False,
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=RedAgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )

    # No manual patching for /.well-known/agent.json needed.
    # A2AStarletteApplication will expose the agent card automatically if compatible.

    return app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Battle Royale Red Agent server with a configurable port.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="TCP port for the HTTP server to listen on (default: 8001)",
    )

    args = parser.parse_args()

    application = build_app(args.port)

    uvicorn.run(application.build(), host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main() 