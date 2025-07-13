#!/usr/bin/env python3
"""
Test the logging functionality of the green agent
"""

import requests
import json
import time
import os
from pathlib import Path

def test_green_agent_logging():
    """Test that the green agent logs events properly"""
    
    green_agent_url = "http://localhost:8011"
    
    print("=== Testing Green Agent Logging ===")
    
    # Test 1: Trigger some events that should be logged
    print("\n1️⃣ Testing battle arena creation (should log)...")
    create_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg_create",
                "role": "user",
                "parts": [{"text": "Please create a battle arena with ID 'test_battle' for 2 red agents"}]
            }
        }
    }
    
    try:
        response = requests.post(
            green_agent_url,
            json=create_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Battle arena creation request sent")
            print(f"Response: {result.get('result', {}).get('artifacts', [{}])[0].get('parts', [{}])[0].get('text', 'No text')[:100]}...")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 2: Start a battle (should log)
    print("\n2️⃣ Testing battle start (should log)...")
    start_request = {
        "jsonrpc": "2.0",
        "id": 2,
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
            json=start_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Battle start request sent")
            print(f"Response: {result.get('result', {}).get('artifacts', [{}])[0].get('parts', [{}])[0].get('text', 'No text')[:100]}...")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(2)
    
    # Test 3: Check uptime (should log)
    print("\n3️⃣ Testing uptime calculation (should log)...")
    uptime_request = {
        "jsonrpc": "2.0",
        "id": 3,
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
            print("✅ Uptime calculation request sent")
            print(f"Response: {result.get('result', {}).get('artifacts', [{}])[0].get('parts', [{}])[0].get('text', 'No text')[:100]}...")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Check if log file was created
    print("\n4️⃣ Checking log file...")
    logs_dir = Path(__file__).parent.parent / "logs"
    log_file = logs_dir / "battle_royale.log"
    
    if log_file.exists():
        print(f"✅ Log file exists: {log_file}")
        
        # Read the last few lines of the log
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(f"📄 Log file has {len(lines)} lines")
                
                if lines:
                    print("📝 Last 5 log entries:")
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
                else:
                    print("   Log file is empty")
                    
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    else:
        print(f"❌ Log file not found: {log_file}")
        print(f"   Logs directory exists: {logs_dir.exists()}")
        if logs_dir.exists():
            print(f"   Logs directory contents: {list(logs_dir.iterdir())}")

if __name__ == "__main__":
    print("=== Green Agent Logging Test ===")
    test_green_agent_logging()
    print("\n=== Test Complete ===") 