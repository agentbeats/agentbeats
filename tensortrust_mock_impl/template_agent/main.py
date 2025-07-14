# -*- coding: utf-8 -*-
"""
A implementation of your new agent
"""

import yaml
import uvicorn
import asyncio
import argparse

# a2a-sdk
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard

# agentbeats SDK
from tensortrust_mock_impl.agentbeats import AgentBeatsExecutor

# ============ User TODO begin ============
user_mcp_url_list = []
user_tool_list = []
# ============ User TODO end ============


async def main() -> None:
    # parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run the Template-Agent server with a configurable port and agent_card.",
    )
    parser.add_argument(
        "--agent-card",
        type=str,
        default="template_agent/template_agent_card.yaml",
        help="Path to the template-agent card YAML file (default: template_agent_card.yaml).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000).",
    )
    args = parser.parse_args()

    # read agent card from YAML file
    with open(args.agent_card, "r", encoding="utf-8") as f:
        agent_card_json = yaml.safe_load(f)
    agent_card = AgentCard(**agent_card_json)

    # create the A2A Starlette application with the agent card and request handler
    application = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=await AgentBeatsExecutor.create(
                agent_card_json=agent_card_json,
                mcp_url_list=user_mcp_url_list,
                tool_list=user_tool_list,
            ),
            task_store=InMemoryTaskStore(),
        ),
    ).build()

    uvicorn_config = uvicorn.Config(
        app=application,
        host="0.0.0.0",
        port=args.port,
        loop="asyncio",
    )
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()


if __name__ == "__main__":
    asyncio.run(main())
