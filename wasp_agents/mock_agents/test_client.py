import asyncio
import httpx
import uuid
from a2a.client import A2AClient
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest

async def test_green_agent_flow():
    """Test the complete flow: Green Agent -> Red Agent -> Result."""
    
    print("🚀 Testing A2A Green Agent Flow")
    print("=" * 50)
    
    # Create A2A client
    async with httpx.AsyncClient() as httpx_client:
        # Get Green Agent's metadata
        print("📋 Getting Green Agent metadata...")
        agent_card_response = await httpx_client.get("http://localhost:10002/.well-known/agent.json")
        agent_card_data = agent_card_response.json()
        agent_card = AgentCard(**agent_card_data)
        
        print(f"✅ Found agent: {agent_card.name}")
        print(f"📝 Description: {agent_card.description}")
        print(f"🔧 Skills: {[skill.name for skill in agent_card.skills]}")
        print()
        
        # Create A2A client
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card
        )
        
        # Send message to Green Agent
        print("🤖 Sending request to Green Agent...")
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': 'Get a number from Red Agent and add 1 to it'}
                ],
                'messageId': uuid.uuid4().hex,
            }
        }
        
        request = SendMessageRequest(
            id=str(uuid.uuid4()),
            params=MessageSendParams(**send_message_payload)
        )
        
        # Send the message
        response = await client.send_message(request)
        
        # Extract and display the result
        print("📊 Processing response...")
        response_dict = response.model_dump(mode='json', exclude_none=True)
        
        if 'result' in response_dict and 'artifacts' in response_dict['result']:
            artifacts = response_dict['result']['artifacts']
            for artifact in artifacts:
                if 'parts' in artifact:
                    for part in artifact['parts']:
                        if 'text' in part:
                            print("🎯 Final Result:")
                            print(f"   {part['text']}")
                            return
        
        print("❌ Could not extract result from response")
        print("📄 Full response:", response_dict)

async def test_red_agent_directly():
    """Test Red Agent directly to verify it works."""
    
    print("\n🔴 Testing Red Agent Directly")
    print("=" * 30)
    
    async with httpx.AsyncClient() as httpx_client:
        # Get Red Agent's metadata
        agent_card_response = await httpx_client.get("http://localhost:10001/.well-known/agent.json")
        agent_card_data = agent_card_response.json()
        agent_card = AgentCard(**agent_card_data)
        
        print(f"✅ Found agent: {agent_card.name}")
        
        # Create A2A client
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card
        )
        
        # Send message to Red Agent
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': 'Tell me a number'}
                ],
                'messageId': uuid.uuid4().hex,
            }
        }
        
        request = SendMessageRequest(
            id=str(uuid.uuid4()),
            params=MessageSendParams(**send_message_payload)
        )
        
        # Send the message
        response = await client.send_message(request)
        
        # Extract and display the result
        response_dict = response.model_dump(mode='json', exclude_none=True)
        
        if 'result' in response_dict and 'artifacts' in response_dict['result']:
            artifacts = response_dict['result']['artifacts']
            for artifact in artifacts:
                if 'parts' in artifact:
                    for part in artifact['parts']:
                        if 'text' in part:
                            print(f"🔢 Red Agent's number: {part['text']}")
                            return
        
        print("❌ Could not extract number from Red Agent")

async def main():
    """Main function to run the tests."""
    try:
        # Test Red Agent first
        await test_red_agent_directly()
        
        # Test the complete flow
        await test_green_agent_flow()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure both agents are running:")
        print("   python red_agent.py  # Port 10001")
        print("   python green_agent.py # Port 10002")

if __name__ == "__main__":
    asyncio.run(main()) 