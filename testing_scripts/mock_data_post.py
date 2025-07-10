import json
import requests
import time

# Backend endpoints
BASE_URL = 'http://localhost:9000'
AGENTS_URL = f'{BASE_URL}/agents'

# Only these agent names will be added
AGENT_NAMES = {"Green Team Agent", "Blue Team Agent", "Red Team Agent"}

# Map agent names to correct 90xx ports
AGENT_PORTS = {
    "Green Team Agent": {"agent_url": "http://localhost:9031", "launcher_url": "http://localhost:9030"},
    "Blue Team Agent": {"agent_url": "http://localhost:9011", "launcher_url": "http://localhost:9010"},
    "Red Team Agent": {"agent_url": "http://localhost:9021", "launcher_url": "http://localhost:9020"},
}

def load_collections_data():
    try:
        with open('src/backend/db/data/collections-export-formatted.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading collections-export-formatted.json: {e}")
        return []

def register_agents(agents_data):
    print("Registering agents (green, blue, red, 90xx ports)...")
    for item in agents_data:
        if item['collection'] == 'agents':
            agent_data = item['data']
            register_info = agent_data['register_info']
            name = register_info.get('name', '')
            if name not in AGENT_NAMES:
                continue
            # Use the mapped 90xx ports
            agent_registration = {
                "name": name,
                "agent_url": AGENT_PORTS[name]["agent_url"],
                "launcher_url": AGENT_PORTS[name]["launcher_url"],
                "is_green": bool(register_info.get('is_green', False))
            }
            # For green agent, always include participant_requirements
            if agent_registration["is_green"]:
                agent_registration['participant_requirements'] = register_info.get('participant_requirements', [])
            print(f"Registering agent: {name} -> {agent_registration['agent_url']}")
            try:
                response = requests.post(AGENTS_URL, json=agent_registration)
                if response.status_code == 201:
                    created_agent = response.json()
                    print(f"✓ Created agent: {created_agent.get('agent_id', 'unknown')}")
                else:
                    print(f"✗ Failed to create agent: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"✗ Error registering agent: {e}")
            time.sleep(0.2)

def main():
    collections_data = load_collections_data()
    if not collections_data:
        print("No data found to load")
        return
    agents_data = [item for item in collections_data if item['collection'] == 'agents']
    print(f"Found {len(agents_data)} agent records in collection")
    register_agents(agents_data)
    print("\n✓ Agent registration complete!")

if __name__ == "__main__":
    main() 