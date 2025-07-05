import asyncio
import httpx
import uuid
from a2a.client import A2AClient
from a2a.types import AgentCard, TextPart, Message, MessageSendParams, SendMessageRequest


async def test_green_agent():
    test_cases = [
        "reset",
        "click(10,20)",
        "click(0,0)",
        "click(100,200)",
        "invalid_action",
        "click(abc,def)",
    ]
    
    async with httpx.AsyncClient() as httpx_client:
        # Get agent card
        agent_card_response = await httpx_client.get("http://localhost:10002/.well-known/agent.json")
        agent_card_data = agent_card_response.json()
        agent_card = AgentCard(**agent_card_data)
        
        # Create A2A client
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        
        for test_input in test_cases:
            try:
                # Create message
                message = Message(
                    role="user",
                    parts=[TextPart(text=test_input)],
                    messageId=uuid.uuid4().hex,
                )
                
                # Create message send params
                params = MessageSendParams(message=message)
                
                # Create send message request
                request = SendMessageRequest(
                    id=str(uuid.uuid4()),
                    params=params
                )
                
                # Send message using A2A client
                response = await client.send_message(request)
                print(f"✅ {test_input}: {response}")
            except Exception as e:
                print(f"❌ {test_input}: {e}")


async def test_agent_card():
    async with httpx.AsyncClient() as httpx_client:
        try:
            agent_card_response = await httpx_client.get("http://localhost:10002/.well-known/agent.json")
            if agent_card_response.status_code == 200:
                agent_card_data = agent_card_response.json()
                agent_card = AgentCard(**agent_card_data)
                print(f"Agent: {agent_card.name}")
                print(f"Skills: {[skill.name for skill in agent_card.skills]}")
            else:
                print(f"Failed to get agent card: {agent_card_response.status_code}")
        except Exception as e:
            print(f"Failed to get agent card: {e}")


if __name__ == "__main__":
    async def main():
        await test_agent_card()
        await test_green_agent()
    
    asyncio.run(main()) 