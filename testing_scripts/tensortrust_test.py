#!/usr/bin/env python
"""
Test script for the Agent Beats Backend API.
This script demonstrates how to use the API endpoints with real agents.
"""
import asyncio
import json
import uuid
import httpx
import sys
from datetime import datetime
import os

BASE_URL = "http://localhost:9000"
MCP_URL = "http://localhost:9001/sse/"

BLUE_LAUNCHER = "http://localhost:9010"
BLUE_URL = "http://localhost:9011"

RED_LAUNCHER = "http://localhost:9020"
RED_URL = "http://localhost:9021"

GREEN_LAUNCHER = "http://localhost:9030"
GREEN_URL = "http://localhost:9031"

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

async def test_api():
    """Test the backend API endpoints with real agents."""
    async with httpx.AsyncClient() as client:
        print("Testing Agent Beats Backend API...")
        
        response = await client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return

        green_agent_id = await register_agent(client, "Green Team Agent", GREEN_URL, GREEN_LAUNCHER, True,
                                              participant_requirements=[{
            "role": "blue_agent",
            "name": "guardrail_generator",
            "required": True
        }, {
            "role": "red_agent",
            "name": "prompt_injector",
            "required": True
                                              }])
        
        blue_agent_id = await register_agent(client, "Blue Team Agent", BLUE_URL, BLUE_LAUNCHER, False)
        red_agent_id = await register_agent(client, "Red Team Agent", RED_URL, RED_LAUNCHER, False)
        
        if not all([green_agent_id, blue_agent_id, red_agent_id]):
            print("❌ Failed to register all agents")
            return
        
        input("Press Enter to continue after agents are registered...")


        print("\nListing all agents:")
        response = await client.get(f"{BASE_URL}/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Found {len(agents)} agents")
            for agent in agents:
                print(f"  - {agent['register_info']['name']} ({agent['agent_id']})")
        else:
            print(f"❌ Failed to list agents: {response.status_code}")

        input("Press Enter to continue after agents are registered...")
                
        # Create a battle
        battle_id = await create_battle(
            client,
            green_agent_id,
            [{
                "agent_id": blue_agent_id,
                "name": "guardrail_generator",
            },
             {
                "agent_id": red_agent_id,
                "name": "prompt_injector",
             }]
        )
        if not battle_id:
            print("❌ Failed to create battle")
            return
        
        input("Press Enter to continue after agents are ready...")

        input("Press Enter to continue, battle is happening...")
        print("\nBattle details:")
        response = await client.get(f"{BASE_URL}/battles/{battle_id}")
        if response.status_code == 200:
            battle = response.json()
            print(f"✅ Battle {battle_id} created")
            print(f"  - State: {battle['state']}")
        else:
            print(f"❌ Failed to get battle details: {response.status_code}")

        input("Press Enter to continue, after battle result is reported...")
                
        # Get updated battle details
        print("\nUpdated battle details:")
        response = await client.get(f"{BASE_URL}/battles/{battle_id}")
        if response.status_code == 200:
            battle = response.json()
            print(f"✅ Battle state: {battle['state']}")
            if "result" in battle:
                print(battle['result'])
                print(battle['state'])
        else:
            print(f"❌ Failed to get updated battle details: {response.status_code}")
                
        print("\nTest completed successfully!")

# async def send_reset(url: str, payload: dict) -> None:
#     """POST a reset signal to *url*."""
#     async with httpx.AsyncClient() as client:
#         resp = await client.post(url, json=payload)
#         resp.raise_for_status()
#     print(f"[reset] sent to {url} -> {resp.status_code}")
#     return resp.json()

# def report_ready(agent_id):
#     """Report that an agent is ready."""
#     print(f"Reporting agent {agent_id} as ready...")
#     info = {
#         'ready': True,
#     }
#     response = httpx.put(f"{BASE_URL}/agents/{agent_id}", json=info)
#     if response.status_code == 204:
#         print(f"✅ Agent {agent_id} is now ready")
#     else:
#         print(f"❌ Failed to report agent {agent_id} as ready: {response.status_code}")
#         print(f"Response content: {response.text}")

# async def report_log(client, message, battle_id):
#     """Report a log message for a battle."""
#     print(f"Reporting log for battle {battle_id}...")
    
#     log_entry = {
#         "message": message,
#         "eventType": "log",
#         "source": "test_api",
#     }
    
#     response = await client.post(
#         f"{BASE_URL}/battles/{battle_id}",
#         json=log_entry
#     )
    
#     if response.status_code == 204:
#         print("✅ Log reported successfully")
#     else:
#         print(f"❌ Failed to report log: {response.status_code}")
#         print(f"Response content: {response.text}")
#     return response.status_code == 204

async def register_agent(client, name, endpoint, launcher, is_green, participant_requirements=None):
    """Register a real agent and return its ID."""
    print(f"\nRegistering {name}...")
    
    # Register the agent
    agent_info = {
        "alias": name,
        "agent_url": endpoint,
        "launcher_url": launcher,  # Assuming a launcher endpoint for the agent
        "is_green": is_green,
    }

    if is_green:
        agent_info["participant_requirements"] = participant_requirements
    
    response = await client.post(
        f"{BASE_URL}/agents",
        json=agent_info
    )
    
    if response.status_code == 201:
        agent = response.json()
        print(f"✅ {name} registered with ID: {agent['agent_id']}")
        return agent['agent_id']
    else:
        print(f"❌ Failed to register {name}: {response.status_code}")
        print(f"Response content: {response.text}")
        return None
        
async def create_battle(client, green_agent_id, opponents):
    """Create a battle and return its ID."""
    print("\nCreating battle...")
    
    battle_request = {
        "green_agent_id": green_agent_id,
        "opponents": opponents,
        "config": {
            "battle_timeout": 300,
            "ready_timeout": 300,            
        },
    }
    
    response = await client.post(
        f"{BASE_URL}/battles",
        json=battle_request
    )
    
    if response.status_code == 201:
        battle = response.json()
        print(f"✅ Battle created with ID: {battle['battle_id']}")
        print("  - Green agent will be notified with blue and red agent cards")
        return battle['battle_id']
    else:
        print(f"❌ Failed to create battle: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

async def main():
    """Run the tests."""
    await test_api()

if __name__ == "__main__":
    asyncio.run(main())
