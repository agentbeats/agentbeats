#!/usr/bin/env python3
"""
Battle Royale Infrastructure Test Script
Tests the Docker container setup, SSH connections, and basic infrastructure.
Consolidated from the redundant parts of test_battle_royale.py and test_battle_royale_agents.py
"""

import asyncio
import json
import time
import subprocess
import sys
from typing import Dict, List, Optional
import logging

# Try to import optional dependencies
try:
    import requests
except ImportError:
    print("❌ requests module not found. Please install: pip install requests")
    sys.exit(1)

try:
    import paramiko
except ImportError:
    print("❌ paramiko module not found. Please install: pip install paramiko")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BattleRoyaleInfrastructureTester:
    def __init__(self):
        self.container_name = "battle-royale-arena"
        self.ssh_host = "localhost"
        self.ssh_port = 2222
        self.ssh_user = "root"
        self.ssh_password = "password123"
        self.web_port = 8080
        self.monitor_port = 8081
        self.battle_arena_url = "http://localhost:8080"
        
    def check_docker_status(self) -> bool:
        """Check if the Docker container is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}"],
                capture_output=True, text=True, check=True
            )
            return self.container_name in result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check Docker status: {e}")
            return False
    
    def start_container(self) -> bool:
        """Start the battle royale container."""
        try:
            logger.info("Starting battle royale container...")
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd="../docker",
                check=True
            )
            time.sleep(5)  # Wait for container to start
            return self.check_docker_status()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start container: {e}")
            return False
    
    def stop_container(self) -> bool:
        """Stop the battle royale container."""
        try:
            logger.info("Stopping battle royale container...")
            subprocess.run(
                ["docker-compose", "down"],
                cwd="../docker",
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop container: {e}")
            return False
    
    def test_ssh_connection(self) -> bool:
        """Test SSH connection to the container."""
        try:
            logger.info("Testing SSH connection...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.ssh_host,
                port=self.ssh_port,
                username=self.ssh_user,
                password=self.ssh_password,
                timeout=10
            )
            ssh.close()
            logger.info("✅ SSH connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ SSH connection failed: {e}")
            return False
    
    def test_monitor_endpoint(self) -> bool:
        """Test the monitor endpoint."""
        try:
            logger.info("Testing monitor endpoint...")
            response = requests.get(f"http://localhost:{self.monitor_port}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Monitor endpoint working: {data}")
                return True
            else:
                logger.error(f"❌ Monitor endpoint returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Monitor endpoint test failed: {e}")
            return False
    
    def test_battle_arena_status(self) -> bool:
        """Test if the battle arena container is running and accessible."""
        try:
            logger.info("Testing Battle Arena status...")
            response = requests.get(f"{self.battle_arena_url}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Battle Arena is running: {data}")
                return True
            else:
                logger.error(f"❌ Battle Arena returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Battle Arena status check failed: {e}")
            return False
    
    def simulate_agent_ssh_session(self, agent_name: str) -> bool:
        """Simulate an agent SSH session."""
        try:
            logger.info(f"Simulating {agent_name} SSH session...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.ssh_host,
                port=self.ssh_port,
                username=self.ssh_user,
                password=self.ssh_password,
                timeout=10
            )
            
            # Execute some basic commands
            commands = [
                "whoami",
                "pwd",
                "ls -la /battle_arena",
                "ps aux | grep -E '(python|node|apache|nginx)'",
                "ss -tuln | grep :80"
            ]
            
            for cmd in commands:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                output = stdout.read().decode().strip()
                logger.info(f"{agent_name} - {cmd}: {output}")
            
            ssh.close()
            logger.info(f"✅ {agent_name} SSH session completed")
            return True
        except Exception as e:
            logger.error(f"❌ {agent_name} SSH session failed: {e}")
            return False
    
    def simulate_web_service_creation(self, agent_name: str) -> bool:
        """Simulate creating a web service for an agent."""
        try:
            logger.info(f"Simulating {agent_name} web service creation...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.ssh_host,
                port=self.ssh_port,
                username=self.ssh_user,
                password=self.ssh_password,
                timeout=10
            )
            
            # Create a simple web service
            service_script = f'''#!/usr/bin/env python3
import http.server
import socketserver

PORT = 80
AGENT_NAME = "{agent_name}"

class AgentHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h1>{{AGENT_NAME}}</h1><p>Service is running!</p>".encode())
        else:
            super().do_GET()

with socketserver.TCPServer(("", PORT), AgentHandler) as httpd:
    print(f"{{AGENT_NAME}} server running on port {{PORT}}")
    httpd.serve_forever()
'''
            
            # Write the service script
            stdin, stdout, stderr = ssh.exec_command(f"echo '{service_script}' > /battle_arena/{agent_name}_service.py")
            if stderr.read():
                logger.error(f"Failed to create service script for {agent_name}")
                return False
            
            # Make it executable
            ssh.exec_command(f"chmod +x /battle_arena/{agent_name}_service.py")
            
            # Start the service in background
            ssh.exec_command(f"nohup python3 /battle_arena/{agent_name}_service.py > /battle_arena/{agent_name}_service.log 2>&1 &")
            
            # Wait a moment for service to start
            time.sleep(2)
            
            # Check if service is running
            stdin, stdout, stderr = ssh.exec_command("ps aux | grep python3 | grep service")
            output = stdout.read().decode().strip()
            if agent_name in output:
                logger.info(f"✅ {agent_name} web service started successfully")
            else:
                logger.warning(f"⚠️ {agent_name} web service may not have started")
            
            ssh.close()
            return True
        except Exception as e:
            logger.error(f"❌ {agent_name} web service creation failed: {e}")
            return False
    
    def test_web_service_access(self, agent_name: str) -> bool:
        """Test accessing a web service."""
        try:
            logger.info(f"Testing web service access for {agent_name}...")
            response = requests.get(f"http://localhost:{self.web_port}/", timeout=10)
            if response.status_code == 200:
                content = response.text
                if agent_name.lower() in content.lower():
                    logger.info(f"✅ {agent_name} web service accessible and serving correct content")
                    return True
                else:
                    logger.warning(f"⚠️ {agent_name} web service accessible but content may be incorrect")
                    return False
            else:
                logger.error(f"❌ {agent_name} web service returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ {agent_name} web service access failed: {e}")
            return False
    
    def run_infrastructure_tests(self) -> Dict[str, bool]:
        """Run the complete infrastructure test suite."""
        results = {}
        
        logger.info("🚀 Starting Battle Royale Infrastructure Test Suite")
        logger.info("=" * 50)
        
        # Test 1: Check if container is running
        logger.info("Test 1: Checking Docker container status...")
        if not self.check_docker_status():
            logger.info("Container not running, attempting to start...")
            results["container_start"] = self.start_container()
        else:
            results["container_start"] = True
        
        if not results["container_start"]:
            logger.error("❌ Failed to start container, aborting tests")
            return results
        
        # Test 2: SSH connection
        logger.info("Test 2: Testing SSH connection...")
        results["ssh_connection"] = self.test_ssh_connection()
        
        # Test 3: Monitor endpoint
        logger.info("Test 3: Testing monitor endpoint...")
        results["monitor_endpoint"] = self.test_monitor_endpoint()
        
        # Test 4: Battle arena status
        logger.info("Test 4: Testing battle arena status...")
        results["battle_arena_status"] = self.test_battle_arena_status()
        
        # Test 5: Simulate multiple agents
        logger.info("Test 5: Simulating multiple agent sessions...")
        agents = ["RedAgent_Alpha", "RedAgent_Beta", "RedAgent_Gamma"]
        
        results["agent_sessions"] = True
        for agent in agents:
            if not self.simulate_agent_ssh_session(agent):
                results["agent_sessions"] = False
        
        # Test 6: Simulate web service creation
        logger.info("Test 6: Simulating web service creation...")
        results["web_service_creation"] = True
        for agent in agents:
            if not self.simulate_web_service_creation(agent):
                results["web_service_creation"] = False
        
        # Test 7: Test web service access
        logger.info("Test 7: Testing web service access...")
        results["web_service_access"] = self.test_web_service_access(agents[0])
        
        # Test 8: Check final status
        logger.info("Test 8: Checking final container status...")
        results["final_status"] = self.test_monitor_endpoint()
        
        logger.info("=" * 50)
        logger.info("📊 Infrastructure Test Results Summary:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        return results

async def main():
    """Main test function."""
    tester = BattleRoyaleInfrastructureTester()
    
    try:
        results = tester.run_infrastructure_tests()
        
        # Calculate overall success
        passed = sum(results.values())
        total = len(results)
        success_rate = (passed / total) * 100
        
        logger.info(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed}/{total})")
        
        if success_rate >= 80:
            logger.info("🎉 Battle Royale infrastructure is working well!")
        elif success_rate >= 60:
            logger.info("⚠️ Battle Royale infrastructure has some issues but is mostly functional")
        else:
            logger.error("❌ Battle Royale infrastructure has significant issues")
        
        # Ask if user wants to stop the container
        response = input("\nDo you want to stop the container? (y/N): ")
        if response.lower() == 'y':
            tester.stop_container()
            logger.info("Container stopped")
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Test interrupted by user")
        tester.stop_container()
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        tester.stop_container()

if __name__ == "__main__":
    asyncio.run(main()) 