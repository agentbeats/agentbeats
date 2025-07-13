#!/usr/bin/env python3
"""
Basic test script for Battle Royale Agents
Tests the agent structure without requiring API keys.
"""

import sys
import os
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "agents"))


def test_agent_structure(agent_type: str):
    """Test the basic structure of an agent without running it."""
    print(f"🔍 Testing {agent_type} agent structure...")
    
    agent_dir = os.path.join(AGENTS_DIR, f"{agent_type}_agent")
    
    # Check if directory exists
    if not os.path.exists(agent_dir):
        print(f"❌ {agent_type} agent directory not found: {agent_dir}")
        return False
    
    # Check required files
    required_files = ["main.py", "agent_executor.py", "prompt.py", "requirements.txt"]
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(agent_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files in {agent_type} agent: {missing_files}")
        return False
    
    # Test importing prompt (this should work without API key)
    try:
        prompt_path = os.path.join(agent_dir, "prompt.py")
        spec = importlib.util.spec_from_file_location("prompt", prompt_path)
        if spec is None:
            print(f"❌ Failed to create spec for {agent_type} agent prompt")
            return False
        prompt_module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            print(f"❌ Failed to get loader for {agent_type} agent prompt")
            return False
        spec.loader.exec_module(prompt_module)
        
        if agent_type == "red":
            if hasattr(prompt_module, 'RED_AGENT_PROMPT'):
                print(f"✅ {agent_type} agent prompt loaded successfully")
            else:
                print(f"❌ {agent_type} agent missing RED_AGENT_PROMPT")
                return False
        elif agent_type == "green":
            if hasattr(prompt_module, 'GREEN_AGENT_PROMPT'):
                print(f"✅ {agent_type} agent prompt loaded successfully")
            else:
                print(f"❌ {agent_type} agent missing GREEN_AGENT_PROMPT")
                return False
        
    except Exception as e:
        print(f"❌ Failed to load {agent_type} agent prompt: {e}")
        return False
    
    # Test that main.py file exists and has basic structure
    main_path = os.path.join(agent_dir, "main.py")
    try:
        with open(main_path, 'r') as f:
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
    """Test that requirements files exist and are readable."""
    print("🔍 Testing requirements files...")
    
    agents = ["red", "green"]
    for agent_type in agents:
        req_file = os.path.join(AGENTS_DIR, f"{agent_type}_agent", "requirements.txt")
        
        if not os.path.exists(req_file):
            print(f"❌ Requirements file not found: {req_file}")
            return False
        
        try:
            with open(req_file, 'r') as f:
                content = f.read()
                if len(content.strip()) > 0:
                    print(f"✅ {agent_type} agent requirements file is valid")
                else:
                    print(f"❌ {agent_type} agent requirements file is empty")
                    return False
        except Exception as e:
            print(f"❌ Failed to read {agent_type} agent requirements: {e}")
            return False
    
    return True

def test_launch_scripts():
    """Test that launch scripts exist and are executable."""
    print("🔍 Testing launch scripts...")
    
    scripts = [
        os.path.join(AGENTS_DIR, "start_red_agent.sh"),
        os.path.join(AGENTS_DIR, "start_green_agent.sh")
    ]
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"❌ Launch script not found: {script}")
            return False
        
        if not os.access(script, os.X_OK):
            print(f"❌ Launch script not executable: {script}")
            return False
        
        print(f"✅ Launch script exists and is executable: {script}")
    
    return True

def run_basic_tests():
    """Run all basic tests."""
    print("🚀 Starting Basic Agent Structure Tests")
    print("=" * 50)
    
    results = {}
    
    # Test agent structures
    results["red_agent_structure"] = test_agent_structure("red")
    results["green_agent_structure"] = test_agent_structure("green")
    
    # Test requirements files
    results["requirements_files"] = test_requirements_files()
    
    # Test launch scripts
    results["launch_scripts"] = test_launch_scripts()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Basic Test Results Summary:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed! Agents are ready for testing with API keys.")
    else:
        print("⚠️  Some tests failed. Please fix the issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1) 