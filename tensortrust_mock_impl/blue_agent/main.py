import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from agent_executor import BlueAgentExecutor


if __name__ == "__main__":
    # ---- 定义公开技能（仅一个“防守”技能即可） --------------------
    defense_skill = AgentSkill(
        id="blue_defense",
        name="Blue Defender",
        description="State-machine defender that reacts to ready/reset/attack signals.",
        tags=["defense", "a2a", "state-machine"],
        examples=["ready", "reset", "attack <payload>"],
    )

    # ---- Agent Card  ---------------------------------------------
    agent_card = AgentCard(
        name="Blue Agent (Defender)",
        description="A2A defender that follows the reset/ready/responsing-attack protocol.",
        url="http://localhost:8001/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[defense_skill],
        supportsAuthenticatedExtendedCard=False,
    )

    # ---- 启动 A2A HTTP 服务 --------------------------------------
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=BlueAgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )

    uvicorn.run(app.build(), host="0.0.0.0", port=8001)
