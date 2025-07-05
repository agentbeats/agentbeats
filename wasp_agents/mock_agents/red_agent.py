import os
import asyncio
import uvicorn
from dotenv import load_dotenv

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
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

class RedAgentExecutor(AgentExecutor):
    """Red Agent that tells a number."""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # Update status
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Thinking of a number...", task.contextId, task.id)
            )
            
            # Call OpenAI to get a number
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides random numbers. When asked for a number, respond with a single integer between 1 and 100. Only respond with the number, no additional text."},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=10
            )
            
            number = response.choices[0].message.content.strip()
            
            # Add response as artifact
            await updater.add_artifact(
                [Part(root=TextPart(text=number))],
                name="number_response"
            )
            
            await updater.complete()
            
        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(f"Error: {str(e)}", task.contextId, task.id),
                final=True
            )
    
    async def cancel(self, task_id: str) -> None:
        """Cancel the execution of a specific task."""
        raise NotImplementedError("Cancellation is not implemented for RedAgentExecutor")

def create_red_agent_server(host="localhost", port=10001):
    """Create A2A server for Red Agent."""
    
    # Agent capabilities
    capabilities = AgentCapabilities(streaming=True)
    
    # Agent card (metadata)
    agent_card = AgentCard(
        name="Red Number Agent",
        description="An agent that tells you a random number",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[
            AgentSkill(
                id="tell_number",
                name="Tell a Number",
                description="Provides a random number between 1 and 100",
                tags=["number", "random", "math"],
                examples=[
                    "Tell me a number",
                    "Give me a random number",
                    "What number do you have?",
                ],
            )
        ],
    )
    
    # Create executor
    executor = RedAgentExecutor()
    
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A application
    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

async def run_red_agent():
    """Run the red agent server."""
    app = create_red_agent_server()
    config = uvicorn.Config(
        app.build(),
        host="127.0.0.1",
        port=10001,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_red_agent()) 