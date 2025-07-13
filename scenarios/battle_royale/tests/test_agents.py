#!/usr/bin/env python3
"""
Merged test script for Battle Royale Agents
Tests agent structure, requirements, agent card, and A2A POST for both agents.
"""

import sys
import os
import importlib.util
import requests
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "agents"))

RED_AGENT_URL = "http://localhost:8001"
GREEN_AGENT_URL = "http://localhost:8011"
AGENT_CARD_PATH = "/.well-known/agent.json"


def test_agent_structure(agent_type: str):
    """Test the basic structure of an agent without running it."""
    print(f"🔍 Testing {agent_type} agent structure...")
    agent_dir = os.path.join(AGENTS_DIR, f"{agent_type}_agent")
    if not os.path.exists(agent_dir):
        print(f"❌ {agent_type} agent directory not found: {agent_dir}")
        return False
    required_files = ["main.py", "agent_executor.py", "prompt.py"]
    missing_files = [file for file in required_files if not os.path.exists(os.path.join(agent_dir, file))]
    if missing_files:
        print(f"❌ Missing files in {agent_type} agent: {missing_files}")
        return False
    try:
        prompt_path = os.path.join(agent_dir, "prompt.py")
        spec = importlib.util.spec_from_file_location("prompt", prompt_path)
        if spec is None or spec.loader is None:
            print(f"❌ Failed to load {agent_type} agent prompt")
            return False
        prompt_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prompt_module)
        if agent_type == "red" and not hasattr(prompt_module, 'RED_AGENT_PROMPT'):
            print(f"❌ {agent_type} agent missing RED_AGENT_PROMPT")
            return False
        if agent_type == "green" and not hasattr(prompt_module, 'GREEN_AGENT_PROMPT'):
            print(f"❌ {agent_type} agent missing GREEN_AGENT_PROMPT")
            return False
        print(f"✅ {agent_type} agent prompt loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load {agent_type} agent prompt: {e}")
        return False
    try:
        with open(os.path.join(agent_dir, "main.py"), 'r') as f:
            content = f.read()
            if "def main()" in content and "build_app" in content:
                print(f"✅ {agent_type} agent main.py has correct structure")
            else:
                print(f"❌ {agent_type} agent main.py missing required functions")
                return False
    except Exception as e:
        print(f"❌ Failed to read {agent_type} agent main.py: {e}")
        return False
    print(f"✅ {agent_type} agent structure is valid")
    return True

def test_requirements_files():
    """Test that the main requirements file exists and is readable."""
    print("🔍 Testing main requirements file...")
    req_file = os.path.join(AGENTS_DIR, "..", "requirements.txt")
    if not os.path.exists(req_file):
        print(f"❌ Main requirements file not found: {req_file}")
        return False
    try:
        with open(req_file, 'r') as f:
            content = f.read()
            if len(content.strip()) > 0:
                print(f"✅ Main requirements file is valid")
            else:
                print(f"❌ Main requirements file is empty")
                return False
    except Exception as e:
        print(f"❌ Failed to read main requirements file: {e}")
        return False
    return True

def test_agent_card(agent_url, agent_name):
    """Test if the agent card is available and valid."""
    print(f"🔍 Testing {agent_name} agent card...")
    try:
        response = requests.get(agent_url + AGENT_CARD_PATH, timeout=10)
        if response.status_code == 200:
            card = response.json()
            print(f"✅ {agent_name} agent card loaded: {card.get('name', 'unknown')}")
            return True
        else:
            print(f"❌ {agent_name} agent card returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {agent_name} agent card check failed: {e}")
        return False

def test_agent_a2a(agent_url, agent_name):
    """Test if the agent responds to a basic A2A POST (should return a JSON-RPC error, but not connection refused)."""
    print(f"🔍 Testing {agent_name} agent A2A POST...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "message/send",
            "params": {"message": {"role": "user", "content": "hello"}}
        }
        response = requests.post(agent_url + "/", json=payload, timeout=10)
        if response.status_code == 200 and response.headers.get("content-type", "").startswith("application/json"):
            print(f"✅ {agent_name} agent A2A POST responded (likely with error, but reachable)")
            return True
        else:
            print(f"❌ {agent_name} agent A2A POST returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {agent_name} agent A2A POST failed: {e}")
        return False

def run_agent_tests():
    """Run all agent tests."""
    print("🚀 Starting Battle Royale Agent Tests (Merged)")
    print("=" * 50)
    results = {}
    # Structure tests
    results["red_agent_structure"] = test_agent_structure("red")
    results["green_agent_structure"] = test_agent_structure("green")
    results["requirements_files"] = test_requirements_files()
    # Agent card and A2A tests
    results["red_agent_card"] = test_agent_card(RED_AGENT_URL, "Red")
    results["green_agent_card"] = test_agent_card(GREEN_AGENT_URL, "Green")
    results["red_agent_a2a"] = test_agent_a2a(RED_AGENT_URL, "Red")
    results["green_agent_a2a"] = test_agent_a2a(GREEN_AGENT_URL, "Green")
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
        print("⚠️  Some agent tests failed. Please fix the issues before proceeding.")
    return passed == total

if __name__ == "__main__":
    success = run_agent_tests()
    sys.exit(0 if success else 1) 