# green_agent.py
import os
import asyncio
import uvicorn
import httpx
import uuid
from dotenv import load_dotenv


from a2a.client import A2AClient
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    MessageSendParams,
    Part,
    SendMessageRequest,
    TaskState,
    TextPart,
)
from a2a.utils import new_agent_text_message, new_task
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()



class GreenAgentExecutor(AgentExecutor):
    """Green Agent that calls Red Agent and adds 1 to the number."""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        # Store red agent URL as attribute
        self.red_agent_url = "http://localhost:10001"
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # Update status
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Calling Red Agent to get a number...", task.contextId, task.id)
            )
            
            # Call Red Agent to get a number
            red_agent_response = await self._call_red_agent("Tell me a number")
            
            # Parse the number from red agent response
            try:
                number = int(red_agent_response.strip())
            except ValueError:
                # If parsing fails, use OpenAI to extract the number
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Extract the number from the given text. Return only the number as an integer."},
                        {"role": "user", "content": f"Extract the number from: {red_agent_response}"}
                    ],
                    temperature=0.1,
                    max_tokens=10
                )
                number = int(response.choices[0].message.content.strip())
            
            # Add 1 to the number
            result = number + 1
            
            # Update status
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(f"Red Agent gave me {number}, adding 1...", task.contextId, task.id)
            )
            
            # Add final result as artifact
            await updater.add_artifact(
                [Part(root=TextPart(text=f"Red Agent gave me {number}. Adding 1 gives us: {result}"))],
                name="final_result"
            )
            
            await updater.complete()
            
        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(f"Error: {str(e)}", task.contextId, task.id),
                final=True
            )
    
    async def _call_red_agent(self, message: str) -> str:
        """Call the red agent directly using its URL."""
        timeout_config = httpx.Timeout(
            timeout=120.0,
            connect=10.0,
            read=120.0,
            write=10.0,
            pool=5.0
        )
        
        async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
            # Get agent card
            agent_card_response = await httpx_client.get(f"{self.red_agent_url}/.well-known/agent.json")
            agent_card_data = agent_card_response.json()
            
            # Create AgentCard from data
            agent_card = AgentCard(**agent_card_data)
            
            # Create A2A client
            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            
            # Build message parameters
            send_message_payload = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': message}
                    ],
                    'messageId': uuid.uuid4().hex,
                }
            }
            
            # Create request
            request = SendMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            # Send message
            response = await client.send_message(request)
            
            # Extract text from response
            try:
                response_dict = response.model_dump(mode='json', exclude_none=True)
                if 'result' in response_dict and 'artifacts' in response_dict['result']:
                    artifacts = response_dict['result']['artifacts']
                    for artifact in artifacts:
                        if 'parts' in artifact:
                            for part in artifact['parts']:
                                if 'text' in part:
                                    return part['text']
                
                return str(response)
            except Exception as e:
                print(f"Error parsing response: {e}")
                return str(response)
    
    async def cancel(self, task_id: str) -> None:
        """Cancel the execution of a specific task."""
        raise NotImplementedError("Cancellation is not implemented for GreenAgentExecutor")

def create_green_agent_server(host="localhost", port=10002):
    """Create A2A server for Green Agent."""
    
    # Agent capabilities
    capabilities = AgentCapabilities(streaming=True)
    
    # Agent card (metadata)
    agent_card = AgentCard(
        name="Green Calculator Agent",
        description="An agent that calls Red Agent to get a number and adds 1 to it",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[
            AgentSkill(
                id="add_one_to_red_number",
                name="Add One to Red Number",
                description="Calls Red Agent to get a number and adds 1 to it",
                tags=["math", "calculation", "addition"],
                examples=[
                    "Get a number from Red Agent and add 1",
                    "Call Red Agent and increment the number",
                    "What's Red Agent's number plus one?",
                ],
            )
        ],
    )
    
    # Create executor
    executor = GreenAgentExecutor()
    
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A application
    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

async def run_green_agent():
    """Run the green agent server."""
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