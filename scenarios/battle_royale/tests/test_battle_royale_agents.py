#!/usr/bin/env python3
"""
Test script for Battle Royale Agents
Tests the red and green agents' API endpoints and functionality.
Focuses only on agent-specific testing, not infrastructure.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
RED_AGENT_URL = "http://localhost:9021"
GREEN_AGENT_URL = "http://localhost:9031"

def test_red_agent_health():
    """Test if the red agent is running and healthy."""
    print("🔍 Testing Red Agent health...")
    try:
        response = requests.get(f"{RED_AGENT_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Red Agent is running")
            return True
        else:
            print(f"❌ Red Agent returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Red Agent health check failed: {e}")
        return False

def test_green_agent_health():
    """Test if the green agent is running and healthy."""
    print("🔍 Testing Green Agent health...")
    try:
        response = requests.get(f"{GREEN_AGENT_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Green Agent is running")
            return True
        else:
            print(f"❌ Green Agent returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Green Agent health check failed: {e}")
        return False

def test_red_agent_ssh_connect():
    """Test the red agent's SSH connection capability."""
    print("🔍 Testing Red Agent SSH connection...")
    try:
        # This would require the red agent to be running and the battle arena container to be up
        # For now, we'll just test if the agent responds
        response = requests.post(f"{RED_AGENT_URL}/", json={
            "message": "Connect to the battle arena via SSH"
        }, timeout=30)
        
        if response.status_code == 200:
            print("✅ Red Agent responded to SSH request")
            return True
        else:
            print(f"❌ Red Agent SSH test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Red Agent SSH test error: {e}")
        return False

def test_green_agent_monitoring():
    """Test the green agent's monitoring capability."""
    print("🔍 Testing Green Agent monitoring...")
    try:
        # Test a short monitoring period (5 seconds instead of 60)
        response = requests.post(f"{GREEN_AGENT_URL}/", json={
            "message": "Monitor web services for 5 seconds"
        }, timeout=30)
        
        if response.status_code == 200:
            print("✅ Green Agent responded to monitoring request")
            return True
        else:
            print(f"❌ Green Agent monitoring test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Green Agent monitoring test error: {e}")
        return False



def run_agent_tests():
    """Run all agent tests."""
    print("🚀 Starting Battle Royale Agent Tests")
    print("=" * 50)
    
    results = {}
    
    # Test agent health (these will fail if agents aren't running)
    results["red_agent_health"] = test_red_agent_health()
    results["green_agent_health"] = test_green_agent_health()
    
    # Test agent capabilities (these will fail if agents aren't running)
    if results["red_agent_health"]:
        results["red_agent_ssh"] = test_red_agent_ssh_connect()
    
    if results["green_agent_health"]:
        results["green_agent_monitoring"] = test_green_agent_monitoring()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Agent Test Results Summary:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All agent tests passed!")
    else:
        print("⚠️  Some agent tests failed. Make sure agents are running.")
    
    return passed == total

if __name__ == "__main__":
    success = run_agent_tests()
    sys.exit(0 if success else 1) 