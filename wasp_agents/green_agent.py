import asyncio
import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
    TaskState,
    TextPart,
)
from a2a.utils import new_agent_text_message, new_task
import re


class GreenAgent(AgentExecutor):
    def __init__(self):
        super().__init__()
        
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Processing game action...", task.contextId, task.id)
            )
            
            if query.lower().strip() == "reset":
                result = "Game reset! Starting fresh."
            elif query.lower().startswith("click"):
                coords_match = re.search(r'click\((\d+),(\d+)\)', query.lower())
                if coords_match:
                    x, y = coords_match.groups()
                    result = f"Clicked at position ({x}, {y})! Dummy response."
                else:
                    result = "Invalid click format. Use click(x,y)"
            else:
                result = f"Unknown action: {query}. Available actions: reset, click(x,y)"
            
            await updater.add_artifact(
                [Part(root=TextPart(text=result))],
                name="game_action_response"
            )
            
            await updater.complete()
            
        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(f"Error: {str(e)}", task.contextId, task.id),
                final=True
            )
    
    async def cancel(self, task_id: str) -> None:
        raise NotImplementedError("Cancellation is not implemented for GreenAgent")


def create_green_agent_server(host="localhost", port=10002):
    capabilities = AgentCapabilities(streaming=True)
    
    agent_card = AgentCard(
        name="Green Game Agent",
        description="An agent that orchestrates game actions like reset and click",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[
            AgentSkill(
                id="game_reset",
                name="Reset Game",
                description="Resets the game to initial state",
                tags=["game", "reset", "control"],
                examples=["reset", "Reset the game", "Start over"],
            ),
            AgentSkill(
                id="game_click",
                name="Click Position",
                description="Handles click actions at specific coordinates",
                tags=["game", "click", "interaction"],
                examples=["click(10,20)", "Click at position 5,15", "click(0,0)"],
            ),
        ],
    )
    
    executor = GreenAgent()
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    
    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )


async def run_green_agent():
    app = create_green_agent_server()
    config = uvicorn.Config(
        app.build(),
        host="127.0.0.1",
        port=10002,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_green_agent())