# -*- coding: utf-8 -*-

"""
A implementation of a blue agent that follows the specification in TensorTrust (https://arxiv.org/abs/2311.01011)
This agent is designed to act as a defender from prompt injection attacks, which generates inpenetrable prompts.
"""

import yaml
import uvicorn
import asyncio
import argparse

from a2a.types import AgentCard
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from tensortrust_mock_impl.agentbeats import AgentBeatsExecutor

# ============ User TODO begin ============
user_mcp_url_list = []
user_tool_list = []
# ============ User TODO end ============


async def main() -> None:
    # parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run the Agent server with a configurable port and agent_card.",
    )
    parser.add_argument(
        "--agent-card",
        type=str,
        default="tensortrust_mock_impl/blue_agent/blue_agent_card.yaml",
        help="Path to the agent card YAML file. (default to blue_agent_card.yaml)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9011,
        help="Port to run the server on. (default: 9011)",
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
