#!/usr/bin/env python3
"""
Comprehensive Battle Royale Test Suite
Tests all components of the battle royale system including agents, Docker arena, and integration.
"""

import asyncio
import json
import time
import requests
import aiohttp
from typing import Dict, List
import subprocess
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class BattleRoyaleTestSuite:
    def __init__(self):
        self.green_agent_url = "http://localhost:8041"
        self.red_agent_urls = [
            "http://localhost:8011",
            "http://localhost:8021",
            "http://localhost:8031"
        ]
        self.docker_arena_url = "http://localhost:9001"
        self.test_results = {}
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results[test_name] = {"success": success, "details": details}
    
    async def test_agent_health(self, agent_url: str, agent_name: str) -> bool:
        """Test if an agent is healthy and responding."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{agent_url}/.well-known/agent.json") as response:
                    if response.status == 200:
                        agent_data = await response.json()
                        self.log_test(f"{agent_name} Health Check", True, 
                                    f"Agent card: {agent_data.get('name', 'Unknown')}")
                        return True
                    else:
                        self.log_test(f"{agent_name} Health Check", False, 
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test(f"{agent_name} Health Check", False, str(e))
            return False
    
    async def test_agent_a2a_communication(self, agent_url: str, agent_name: str) -> bool:
        """Test A2A communication with an agent."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "messages": [{
                        "role": "user",
                        "content": "Hello, this is a test message."
                    }]
                }
                async with session.post(f"{agent_url}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_test(f"{agent_name} A2A Communication", True,
                                    f"Response received: {len(str(result))} chars")
                        return True
                    else:
                        self.log_test(f"{agent_name} A2A Communication", False,
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test(f"{agent_name} A2A Communication", False, str(e))
            return False
    
    async def test_green_agent_tools(self) -> bool:
        """Test green agent's MCP tools."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test Docker management
                payload = {
                    "messages": [{
                        "role": "user",
                        "content": "Check if the Docker battle arena is running."
                    }]
                }
                async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_test("Green Agent Docker Tools", True,
                                    "Docker management tools working")
                        return True
                    else:
                        self.log_test("Green Agent Docker Tools", False,
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Green Agent Docker Tools", False, str(e))
            return False
    
    async def test_red_agent_tools(self) -> bool:
        """Test red agent's MCP tools."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test SSH connection
                payload = {
                    "messages": [{
                        "role": "user",
                        "content": "Test SSH connection to the battle arena."
                    }]
                }
                async with session.post(f"{self.red_agent_urls[0]}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_test("Red Agent SSH Tools", True,
                                    "SSH tools working")
                        return True
                    else:
                        self.log_test("Red Agent SSH Tools", False,
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Red Agent SSH Tools", False, str(e))
            return False
    
    def test_docker_arena(self) -> bool:
        """Test Docker battle arena."""
        try:
            # Test health endpoint
            response = requests.get(f"{self.docker_arena_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Docker Arena Health", True, "Arena is running")
                return True
            else:
                self.log_test("Docker Arena Health", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Docker Arena Health", False, str(e))
            return False
    
    def test_docker_services(self) -> bool:
        """Test Docker services are running."""
        try:
            # Check if docker-compose services are running
            result = subprocess.run(
                ["docker-compose", "ps"],
                cwd="../docker",
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                services_output = result.stdout
                if "Up" in services_output:
                    self.log_test("Docker Services", True, "Services are running")
                    return True
                else:
                    self.log_test("Docker Services", False, "No services running")
                    return False
            else:
                self.log_test("Docker Services", False, "Failed to check services")
                return False
        except Exception as e:
            self.log_test("Docker Services", False, str(e))
            return False
    
    async def test_battle_arena_creation(self) -> bool:
        """Test battle arena creation via green agent."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "messages": [{
                        "role": "user",
                        "content": "Create a test battle arena."
                    }]
                }
                async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_test("Battle Arena Creation", True,
                                    "Arena creation successful")
                        return True
                    else:
                        self.log_test("Battle Arena Creation", False,
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Battle Arena Creation", False, str(e))
            return False
    
    async def test_agent_communication(self) -> bool:
        """Test communication between green and red agents."""
        try:
            async with aiohttp.ClientSession() as session:
                # Green agent sends message to red agent
                payload = {
                    "messages": [{
                        "role": "user",
                        "content": "Send a test message to red agent 1."
                    }]
                }
                async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_test("Agent Communication", True,
                                    "Green agent can communicate with red agents")
                        return True
                    else:
                        self.log_test("Agent Communication", False,
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Agent Communication", False, str(e))
            return False
    
    async def test_web_service_creation(self) -> bool:
        """Test web service creation by red agent."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "messages": [{
                        "role": "user",
                        "content": "Create a test web service on port 8080."
                    }]
                }
                async with session.post(f"{self.red_agent_urls[0]}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_test("Web Service Creation", True,
                                    "Service creation initiated")
                        return True
                    else:
                        self.log_test("Web Service Creation", False,
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Web Service Creation", False, str(e))
            return False
    
    async def test_service_monitoring(self) -> bool:
        """Test service monitoring by green agent."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "messages": [{
                        "role": "user",
                        "content": "Monitor all web services and provide status."
                    }]
                }
                async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_test("Service Monitoring", True,
                                    "Monitoring system working")
                        return True
                    else:
                        self.log_test("Service Monitoring", False,
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Service Monitoring", False, str(e))
            return False
    
    async def test_battle_orchestration(self) -> bool:
        """Test battle orchestration flow."""
        try:
            # Test battle start
            async with aiohttp.ClientSession() as session:
                payload = {
                    "messages": [{
                        "role": "user",
                        "content": "Start a test battle with 30-second duration."
                    }]
                }
                async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_test("Battle Orchestration", True,
                                    "Battle orchestration working")
                        return True
                    else:
                        self.log_test("Battle Orchestration", False,
                                    f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Battle Orchestration", False, str(e))
            return False
    
    def save_test_results(self):
        """Save test results to file."""
        results = {
            "timestamp": time.time(),
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results.values() if r["success"]),
                "failed": sum(1 for r in self.test_results.values() if not r["success"])
            },
            "results": self.test_results
        }
        
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Test Summary:")
        print(f"   Total: {results['summary']['total_tests']}")
        print(f"   Passed: {results['summary']['passed']}")
        print(f"   Failed: {results['summary']['failed']}")
        print(f"   Results saved to: test_results.json")
    
    async def run_all_tests(self):
        """Run all tests in the suite."""
        print("🧪 BATTLE ROYALE COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        
        # Agent Health Tests
        print("\n🔍 Agent Health Tests:")
        await self.test_agent_health(self.green_agent_url, "Green Agent")
        for i, url in enumerate(self.red_agent_urls):
            await self.test_agent_health(url, f"Red Agent {i+1}")
        
        # Agent Communication Tests
        print("\n💬 Agent Communication Tests:")
        await self.test_agent_a2a_communication(self.green_agent_url, "Green Agent")
        for i, url in enumerate(self.red_agent_urls):
            await self.test_agent_a2a_communication(url, f"Red Agent {i+1}")
        
        # Tool Tests
        print("\n🛠️  Tool Tests:")
        await self.test_green_agent_tools()
        await self.test_red_agent_tools()
        
        # Docker Tests
        print("\n🐳 Docker Tests:")
        self.test_docker_arena()
        self.test_docker_services()
        
        # Integration Tests
        print("\n🔗 Integration Tests:")
        await self.test_battle_arena_creation()
        await self.test_agent_communication()
        await self.test_web_service_creation()
        await self.test_service_monitoring()
        await self.test_battle_orchestration()
        
        # Save results
        self.save_test_results()
        
        # Final summary
        passed = sum(1 for r in self.test_results.values() if r["success"])
        total = len(self.test_results)
        
        if passed == total:
            print(f"\n🎉 All {total} tests passed!")
            return True
        else:
            print(f"\n⚠️  {passed}/{total} tests passed. Check test_results.json for details.")
            return False

async def main():
    """Main test runner."""
    test_suite = BattleRoyaleTestSuite()
    success = await test_suite.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 