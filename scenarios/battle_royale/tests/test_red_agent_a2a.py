#!/usr/bin/env python3
"""
Test red agent via A2A protocol
"""

import requests
import json
import time

def test_red_agent_a2a():
    """Test red agent via A2A protocol"""
    
    red_agent_url = "http://localhost:8011"
    
    # Test 1: Ask agent to connect to battle arena
    print("=== Test 1: SSH Connection ===")
    ssh_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_ssh",
                "role": "user",
                "parts": [{"text": "Please connect to the battle arena via SSH using host localhost, port 2222, username battle, and password battle123"}]
            }
        }
    }
    
    try:
        response = requests.post(
            red_agent_url,
            json=ssh_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ SSH connection request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 2: Ask agent to execute a simple command
    print("\n=== Test 2: Command Execution ===")
    cmd_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_cmd",
                "role": "user",
                "parts": [{"text": "Please execute the command 'echo Hello from SSH && whoami && pwd' in the battle arena"}]
            }
        }
    }
    
    try:
        response = requests.post(
            red_agent_url,
            json=cmd_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Command execution request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 3: Ask agent to check service status
    print("\n=== Test 3: Service Status ===")
    status_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_status",
                "role": "user",
                "parts": [{"text": "Please check the status of your web service and other services in the battle arena"}]
            }
        }
    }
    
    try:
        response = requests.post(
            red_agent_url,
            json=status_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Status check request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== Red Agent A2A Test ===")
    test_red_agent_a2a()
    print("\n=== Test Complete ===") 