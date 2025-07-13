#!/usr/bin/env python3
"""
Test green agent tools - Docker monitoring and communication
"""

import requests
import json
import time

def test_green_agent_agent_card():
    """Test green agent agent card endpoint"""
    
    green_agent_url = "http://localhost:8011"
    
    print("=== Test 1: Green Agent Card ===")
    
    try:
        response = requests.get(f"{green_agent_url}/.well-known/agent.json", timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            agent_card = response.json()
            print("✅ Green agent card retrieved successfully")
            print(f"Agent name: {agent_card.get('name', 'Unknown')}")
            print(f"Description: {agent_card.get('description', 'No description')}")
            print(f"Skills: {len(agent_card.get('skills', []))} skills found")
        else:
            print(f"❌ Failed to get agent card: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting agent card: {e}")

def test_green_agent_a2a_message():
    """Test green agent via A2A protocol"""
    
    green_agent_url = "http://localhost:8011"
    
    print("\n=== Test 2: Green Agent A2A Communication ===")
    
    # Test basic communication
    message_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_green_test",
                "role": "user",
                "parts": [{"text": "Hello green agent! Can you check the Docker container status?"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=message_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Green agent responded successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_green_agent_docker_tools():
    """Test green agent Docker monitoring tools"""
    
    green_agent_url = "http://localhost:8011"
    
    print("\n=== Test 3: Green Agent Docker Tools ===")
    
    # Test Docker container status check
    docker_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_docker_check",
                "role": "user",
                "parts": [{"text": "Please check the status of the battle royale Docker container and list any running services"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=docker_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Docker check request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_green_agent_service_monitoring():
    """Test green agent service monitoring capabilities"""
    
    green_agent_url = "http://localhost:8011"
    
    print("\n=== Test 4: Green Agent Service Monitoring ===")
    
    # Test service monitoring
    monitoring_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_monitoring",
                "role": "user",
                "parts": [{"text": "Please monitor all web services in the battle arena and calculate their uptime percentages"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=monitoring_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Service monitoring request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_green_agent_communication():
    """Test green agent communication with red agents"""
    
    green_agent_url = "http://localhost:8011"
    
    print("\n=== Test 5: Green Agent Communication ===")
    
    # Test communication with red agent
    comm_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_communication",
                "role": "user",
                "parts": [{"text": "Please send a message to the red agent at http://localhost:8001 asking for their service status"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=comm_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Communication request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== Green Agent Tools Test ===")
    
    # Wait for green agent to start
    print("Waiting for green agent to start...")
    time.sleep(3)
    
    # Run all tests
    test_green_agent_agent_card()
    test_green_agent_a2a_message()
    test_green_agent_docker_tools()
    test_green_agent_service_monitoring()
    test_green_agent_communication()
    
    print("\n=== Test Complete ===") 