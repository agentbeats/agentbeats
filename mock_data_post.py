import subprocess
import json
import time
import random

# Backend endpoints
AGENTS_URL = 'http://localhost:9000/agents'
USERS_URL = 'http://localhost:9000/users'

def delete_all_users():
    print("Deleting all users...")
    result = subprocess.run([
        'curl', '-s', '-X', 'DELETE', USERS_URL
    ], capture_output=True, text=True)
    print(f"Delete response: {result.stdout}")

def make_mock_users_with_random_agents():
    # Fetch all agent IDs from backend
    result = subprocess.run([
        'curl', '-s', AGENTS_URL
    ], capture_output=True, text=True)
    agents_data = json.loads(result.stdout)
    agent_ids = [a['id'] for a in agents_data if 'id' in a]

    mock_users = [
        {
            "username": "alice",
            "password": "password123",
            "email": "alice@example.com",
            "full_name": "Alice Anderson",
        },
        {
            "username": "bob",
            "password": "securepass",
            "email": "bob@example.com",
            "full_name": "Bob Brown",
        },
        {
            "username": "carol",
            "password": "carolpw",
            "email": "carol@example.com",
            "full_name": "Carol Clark",
        }
    ]
    for user in mock_users:
        n = random.randint(1, 2)
        selected = random.sample(agent_ids, n) if len(agent_ids) >= n else agent_ids
        user["agents"] = {str(aid): True for aid in selected}
        print(f"Creating user: {user['username']} with agents: {list(user['agents'].keys())}")
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', USERS_URL,
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(user)
        ], capture_output=True, text=True)
        try:
            response = json.loads(result.stdout)
            user_id = response.get('id')
            if user_id:
                print(f"Created user with id: {user_id}")
            else:
                print(f"Failed to get user id from response: {response}")
        except Exception as e:
            print(f"Error creating user: {e}")
        time.sleep(0.2)

if __name__ == "__main__":
    delete_all_users()
    make_mock_users_with_random_agents() 