#!/usr/bin/env python3
"""
Test red agent SSH command execution
"""

import requests
import json
import time

def test_red_agent_ssh_command():
    """Test that red agent can execute SSH commands and receive results"""
    
    # Red agent endpoint
    red_agent_url = "http://localhost:8001"
    
    # Test SSH command execution
    ssh_command = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "execute_ssh_command",
            "arguments": {
                "command": "echo 'Hello from SSH!' && whoami && pwd"
            }
        }
    }
    
    print("Testing red agent SSH command execution...")
    print(f"Command: {ssh_command['params']['arguments']['command']}")
    
    try:
        response = requests.post(
            f"{red_agent_url}/a2a",
            json=ssh_command,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Result: {json.dumps(result, indent=2)}")
            
            if "result" in result and "content" in result["result"]:
                print("✅ SSH command executed successfully!")
                print(f"Output: {result['result']['content']}")
            else:
                print("❌ Unexpected response format")
                print(f"Full response: {result}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_red_agent_ssh_connection():
    """Test SSH connection status"""
    
    red_agent_url = "http://localhost:8001"
    
    # Test SSH connection check
    ssh_check = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "check_ssh_connection",
            "arguments": {}
        }
    }
    
    print("\nTesting SSH connection status...")
    
    try:
        response = requests.post(
            f"{red_agent_url}/a2a",
            json=ssh_check,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SSH connection result: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ SSH check failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ SSH check request failed: {e}")

if __name__ == "__main__":
    print("=== Red Agent SSH Command Test ===")
    
    # Wait a moment for agent to start
    print("Waiting for red agent to start...")
    time.sleep(3)
    
    # Test SSH connection first
    test_red_agent_ssh_connection()
    
    # Test SSH command execution
    test_red_agent_ssh_command()
    
    print("\n=== Test Complete ===") 