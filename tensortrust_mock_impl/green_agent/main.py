# -*- coding: utf-8 -*-
"""
An implementation of a green agent that acts as the judge of the blue & red agents
follows the specification in TensorTrust (https://arxiv.org/abs/2311.01011).

This agent hosts the game between the blue and red agents and decides the winner
based on the game rules. It also provides a reset skill that can reset its own
state and the states of the blue and red agents when needed.
"""

import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from agent_executor import GreenAgentExecutor


if __name__ == "__main__":
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
        url="http://localhost:10001/",
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
                blue_agent_url="http://localhost:8001/",
                red_agent_url="http://localhost:9001/",
            ),
            task_store=InMemoryTaskStore(),
        ),
    )

    uvicorn.run(app.build(), host="0.0.0.0", port=10001)
