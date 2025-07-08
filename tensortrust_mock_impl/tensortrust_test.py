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

BASE_URL = "http://localhost:3001"
GREEN_URL = "http://localhost:7001"
GREEN_LAUNCHER = "http://localhost:7000"
BLUE_URL = "http://localhost:8001"
BLUE_LAUNCHER = "http://localhost:8000"
RED_URL = "http://localhost:9001"
RED_LAUNCHER = "http://localhost:9000"

MCP_URL = "http://0.0.0.0:6000/sse/"

# RESET_RED_BLUE_PAYLOAD = {"signal": "reset", "agent_id": None}
# RESET_GREEN_PAYLOAD = {
#     "signal": "reset", 
#     "extra_args": {
#         "mcp-url": "http://0.0.0.0:6000/sse/"
#     }, 
#     "agent_id": None
# }

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

        green_agent_id = await register_agent(client, "Green Team Agent", GREEN_URL, GREEN_LAUNCHER)
        blue_agent_id = await register_agent(client, "Blue Team Agent", BLUE_URL, BLUE_LAUNCHER)
        red_agent_id = await register_agent(client, "Red Team Agent", RED_URL, RED_LAUNCHER)
        
        if not all([green_agent_id, blue_agent_id, red_agent_id]):
            print("❌ Failed to register all agents")
            return
        
        # blue_result = await send_reset(BLUE_LAUNCHER + "/reset", payload={"signal": "reset", "agent_id": blue_agent_id})
        # red_result = await send_reset(RED_LAUNCHER + "/reset", payload={"signal": "reset", "agent_id": red_agent_id})
        # green_result = await send_reset(GREEN_LAUNCHER + "/reset", payload={
        #     "signal": "reset", 
        #     "extra_args": {
        #         "mcp-url": "http://localhost:6000/sse/"
        #     }, 
        #     "agent_id": green_agent_id
        # })
        # if not all([blue_result, red_result, green_result]):
        #     print("❌ Failed to reset all agents")
        #     return
        
        input("Press Enter to continue after agents are registered...")


        print("\nListing all agents:")
        response = await client.get(f"{BASE_URL}/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Found {len(agents)} agents")
            for agent in agents:
                print(f"  - {agent['registerInfo']['name']} ({agent['id']})")
        else:
            print(f"❌ Failed to list agents: {response.status_code}")

        input("Press Enter to continue after agents are registered...")
                
        # Create a battle
        battle_id = await create_battle(
            client,
            green_agent_id,
            [blue_agent_id, red_agent_id]
        )
        if not battle_id:
            print("❌ Failed to create battle")
            return
        
        input("Press Enter to continue after agents are ready...")
        # for agent_id in [green_agent_id, blue_agent_id, red_agent_id]:
        #     report_ready(agent_id)
        # print("All agents reported as ready")

        input("Press Enter to continue, battle is happening...")
        # Get battle details
        print("\nBattle details:")
        response = await client.get(f"{BASE_URL}/battles/{battle_id}")
        if response.status_code == 200:
            battle = response.json()
            print(f"✅ Battle {battle_id} created")
            print(f"  - State: {battle['state']}")
            print(f"  - Green Agent: {battle['greenAgentId']}")
            print(f"  - Opponents: {', '.join(battle['opponents'])}")
        else:
            print(f"❌ Failed to get battle details: {response.status_code}")

        # response = await report_log(client, "Test log message for battle", battle_id)
        # if response:
        #     print("✅ Log reported successfully")
        # else:
        #     print("❌ Failed to report log")
                
        # # Simulate battle result reporting
        # print("\nSimulating battle result reporting...")
        # battle_result = {
        #     "winner": blue_agent_id,
        #     "score": {
        #         "blueScore": 10,
        #         "redScore": 5
        #     },
        #     "detail": {
        #         "rounds": 3,
        #         "log": "Battle completed successfully"
        #     },
        #     "reportedAt": datetime.utcnow().isoformat(),
        #     "eventType": "result",
        # }
        
        # response = await client.post(
        #     f"{BASE_URL}/battles/{battle_id}",
        #     json=battle_result
        # )
        # if response.status_code == 204:
        #     print("✅ Battle result reported successfully")
        # else:
        #     print(f"❌ Failed to report battle result: {response.status_code}")

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

async def send_reset(url: str, payload: dict) -> None:
    """POST a reset signal to *url*."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
    print(f"[reset] sent to {url} -> {resp.status_code}")
    return resp.json()

def report_ready(agent_id):
    """Report that an agent is ready."""
    print(f"Reporting agent {agent_id} as ready...")
    info = {
        'ready': True,
    }
    response = httpx.put(f"{BASE_URL}/agents/{agent_id}", json=info)
    if response.status_code == 204:
        print(f"✅ Agent {agent_id} is now ready")
    else:
        print(f"❌ Failed to report agent {agent_id} as ready: {response.status_code}")
        print(f"Response content: {response.text}")

async def report_log(client, message, battle_id):
    """Report a log message for a battle."""
    print(f"Reporting log for battle {battle_id}...")
    
    log_entry = {
        "message": message,
        "eventType": "log",
        "source": "test_api",
    }
    
    response = await client.post(
        f"{BASE_URL}/battles/{battle_id}",
        json=log_entry
    )
    
    if response.status_code == 204:
        print("✅ Log reported successfully")
    else:
        print(f"❌ Failed to report log: {response.status_code}")
        print(f"Response content: {response.text}")
    return response.status_code == 204

async def register_agent(client, name, endpoint, launcher):
    """Register a real agent and return its ID."""
    print(f"\nRegistering {name}...")
    
    # Register the agent
    agent_info = {
        "name": name,
        "endpoint": endpoint,
        "launcher": launcher,  # Assuming a launcher endpoint for the agent
        "meta": {
            "type": name.split()[0].lower()  # green, blue, or red
        }
    }
    
    response = await client.post(
        f"{BASE_URL}/agents",
        json=agent_info
    )
    
    if response.status_code == 201:
        agent = response.json()
        print(f"✅ {name} registered with ID: {agent['id']}")
        return agent['id']
    else:
        print(f"❌ Failed to register {name}: {response.status_code}")
        print(f"Response content: {response.text}")
        return None
        
async def create_battle(client, green_agent_id, opponent_ids):
    """Create a battle and return its ID."""
    print("\nCreating battle...")
    
    battle_request = {
        "greenAgentId": green_agent_id,
        "opponents": opponent_ids,
        "config": {
            "timeout": 300,
            "readyTimeout": 300,
            # "readyTimeout": 20,
            
        },
        'eventType': 'result'
    }
    
    response = await client.post(
        f"{BASE_URL}/battles",
        json=battle_request
    )
    
    if response.status_code == 201:
        battle = response.json()
        print(f"✅ Battle created with ID: {battle['id']}")
        print("  - Green agent will be notified with blue and red agent cards")
        return battle['id']
    else:
        print(f"❌ Failed to create battle: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

async def main():
    """Run the tests."""
    await test_api()

if __name__ == "__main__":
    asyncio.run(main())
