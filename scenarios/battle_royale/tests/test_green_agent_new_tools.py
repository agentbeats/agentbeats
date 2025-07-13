#!/usr/bin/env python3
"""
Test the new green agent tools: uptime tracking, winner determination, and battle summary
"""

import requests
import json
import time

def test_green_agent_new_tools():
    """Test the new green agent tools"""
    
    green_agent_url = "http://localhost:8011"
    
    print("=== Testing New Green Agent Tools ===")
    
    # Test 1: Uptime tracking (before battle starts)
    print("\n1️⃣ Testing uptime tracking (before battle)...")
    uptime_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_uptime",
                "role": "user",
                "parts": [{"text": "Please calculate uptime percentages for all agents"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=uptime_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Uptime tracking request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 2: Winner determination (before battle starts)
    print("\n2️⃣ Testing winner determination (before battle)...")
    winner_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_winner",
                "role": "user",
                "parts": [{"text": "Please determine the winner of the battle"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=winner_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Winner determination request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 3: Battle summary (before battle starts)
    print("\n3️⃣ Testing battle summary (before battle)...")
    summary_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_summary",
                "role": "user",
                "parts": [{"text": "Please generate a comprehensive battle summary"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=summary_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Battle summary request sent successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 4: Start a battle and then test tools
    print("\n4️⃣ Testing tools after starting a battle...")
    
    # First start a battle
    start_battle_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_start",
                "role": "user",
                "parts": [{"text": "Please start a battle with duration 1 minute"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=start_battle_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Battle start response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Battle started successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Now test uptime tracking during battle
            time.sleep(2)
            print("\n5️⃣ Testing uptime tracking during battle...")
            
            uptime_during_request = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": "msg_uptime_during",
                        "role": "user",
                        "parts": [{"text": "Please calculate uptime percentages for all agents"}]
                    }
                }
            }
            
            response = requests.post(
                green_agent_url,
                json=uptime_during_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"Uptime during battle response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("✅ Uptime tracking during battle successful")
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Uptime during battle failed: {response.text}")
                
        else:
            print(f"❌ Battle start failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during battle test: {e}")

if __name__ == "__main__":
    print("=== Green Agent New Tools Test ===")
    test_green_agent_new_tools()
    print("\n=== Test Complete ===") 