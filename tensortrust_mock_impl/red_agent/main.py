import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from agent_executor import RedAgentExecutor


if __name__ == "__main__":
    attack_skill = AgentSkill(
        id="red_attack",
        name="Red Attacker",
        description="State-machine attacker that auto-generates malicious payloads.",
        tags=["attack", "a2a", "state-machine"],
        examples=["ready", "reset"],
    )

    agent_card = AgentCard(
        name="Red Agent (Attacker)",
        description="A2A attacker that follows the reset/ready/committing-attack protocol.",
        url="http://localhost:8002/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[attack_skill],
        supportsAuthenticatedExtendedCard=False,
    )

    # launch a2a server
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=RedAgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )

    uvicorn.run(app.build(), host="0.0.0.0", port=8002)
