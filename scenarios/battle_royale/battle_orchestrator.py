#!/usr/bin/env python3
"""
Enhanced Battle Royale Orchestrator
Manages the complete battle royale simulation with improved error handling and logging.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import requests
import itertools
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('battle_royale.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BattleOrchestrator:
    def __init__(self):
        # Use the correct child port for the green agent
        self.green_agent_url = "http://localhost:8041"
        self.red_agent_urls = [
            ("http://localhost:8010", "http://localhost:8011"),
            ("http://localhost:8020", "http://localhost:8021"),
            ("http://localhost:8030", "http://localhost:8031")
        ]
        self.docker_arena_url = "http://localhost:9001"
        self.battle_duration = 60  # 1 minute
        self.monitoring_interval = 30  # 30 seconds
        self.rpc_id_counter = itertools.count(1)
        
    async def check_agent_health(self, agent_url: str) -> bool:
        """Check if an agent is healthy and responding."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{agent_url}/.well-known/agent.json") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed for {agent_url}: {e}")
            return False
    
    async def check_docker_arena(self) -> bool:
        """Check if Docker arena is running."""
        try:
            response = requests.get(f"{self.docker_arena_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Docker arena health check failed: {e}")
            return False
    
    async def start_docker_arena(self):
        """Start the Docker battle arena."""
        logger.info("Starting Docker battle arena...")
        try:
            # Start docker-compose
            import subprocess
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd="docker",
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("Docker arena started successfully")
                # Wait for services to be ready
                await asyncio.sleep(10)
                return True
            else:
                logger.error(f"Failed to start Docker arena: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error starting Docker arena: {e}")
            return False
    
    async def create_battle_arena(self) -> bool:
        """Create battle arena via green agent."""
        logger.info("Creating battle arena...")
        try:
            async with aiohttp.ClientSession() as session:
                rpc_id = next(self.rpc_id_counter)
                payload = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "method": "message/send",
                    "params": {
                        "message": {
                            "messageId": uuid.uuid4().hex,
                            "role": "user",
                            "parts": [{"text": "Create a new battle arena for the red agents to compete in."}]
                        }
                    }
                }
                logger.info(f"[DEBUG] Posting to {self.green_agent_url}/ with payload: {json.dumps(payload)}")
                async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                    logger.info(f"[DEBUG] Response status: {response.status}")
                    try:
                        resp_text = await response.text()
                        logger.info(f"[DEBUG] Response body: {resp_text}")
                    except Exception as e:
                        logger.info(f"[DEBUG] Could not read response body: {e}")
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Battle arena created: {result}")
                        return True
                    else:
                        logger.error(f"Failed to create battle arena: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Exception in create_battle_arena: {e}")
            return False
    
    async def start_red_agents(self) -> List[bool]:
        """Start all red agents."""
        logger.info("Starting red agents...")
        results = []
        for i, (launcher_url, agent_url) in enumerate(self.red_agent_urls):
            try:
                # Check if agent is already running
                if await self.check_agent_health(agent_url):
                    logger.info(f"Red agent {i+1} already running")
                    results.append(True)
                    continue
                
                # Start agent (this would typically be done via subprocess)
                logger.info(f"Starting red agent {i+1}...")
                # For now, assume agents are started manually
                await asyncio.sleep(2)
                results.append(True)
            except Exception as e:
                logger.error(f"Failed to start red agent {i+1}: {e}")
                results.append(False)
        return results
    
    async def start_battle(self) -> bool:
        """Start the battle via green agent."""
        logger.info("Starting battle...")
        try:
            async with aiohttp.ClientSession() as session:
                rpc_id = next(self.rpc_id_counter)
                payload = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "method": "message/send",
                    "params": {
                        "message": {
                            "messageId": uuid.uuid4().hex,
                            "role": "user",
                            "parts": [{"text": "Start the battle royale competition. Red agents should now begin creating their web services."}]
                        }
                    }
                }
                async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Battle started: {result}")
                        return True
                    else:
                        logger.error(f"Failed to start battle: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error starting battle: {e}")
            return False
    
    async def monitor_battle(self) -> Dict:
        """Monitor the battle progress."""
        logger.info("Starting battle monitoring...")
        start_time = time.time()
        monitoring_data = []
        
        while time.time() - start_time < self.battle_duration:
            try:
                # Get battle status from green agent
                async with aiohttp.ClientSession() as session:
                    rpc_id = next(self.rpc_id_counter)
                    payload = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "method": "message/send",
                        "params": {
                            "message": {
                                "messageId": uuid.uuid4().hex,
                                "role": "user",
                                "parts": [{"text": "Provide current battle status and scores."}]
                            }
                        }
                    }
                    async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            monitoring_data.append({
                                "timestamp": datetime.now().isoformat(),
                                "status": result
                            })
                            logger.info(f"Battle status: {result}")
                        else:
                            logger.warning(f"Failed to get battle status: {response.status}")
                
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                await asyncio.sleep(self.monitoring_interval)
        
        return {"monitoring_data": monitoring_data, "duration": self.battle_duration}
    
    async def end_battle(self) -> Dict:
        """End the battle and determine winner."""
        logger.info("Ending battle...")
        try:
            async with aiohttp.ClientSession() as session:
                rpc_id = next(self.rpc_id_counter)
                payload = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "method": "message/send",
                    "params": {
                        "message": {
                            "messageId": uuid.uuid4().hex,
                            "role": "user",
                            "parts": [{"text": "End the battle and determine the winner based on service uptime and performance."}]
                        }
                    }
                }
                async with session.post(f"{self.green_agent_url}/", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Battle ended: {result}")
                        return result
                    else:
                        logger.error(f"Failed to end battle: {response.status}")
                        return {"error": "Failed to end battle"}
        except Exception as e:
            logger.error(f"Error ending battle: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Clean up resources after battle."""
        logger.info("Cleaning up...")
        try:
            # Stop docker-compose
            import subprocess
            result = subprocess.run(
                ["docker-compose", "down"],
                cwd="docker",
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("Docker arena cleaned up successfully")
            else:
                logger.warning(f"Docker cleanup warning: {result.stderr}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def check_a2a_endpoint(self) -> bool:
        """Check if the / endpoint is available on the green agent (was /a2a)."""
        try:
            async with aiohttp.ClientSession() as session:
                test_payload = {"messages": [{"role": "user", "content": "ping"}]}
                async with session.post(f"{self.green_agent_url}/", json=test_payload) as response:
                    logger.info(f"[DEBUG] / endpoint check status: {response.status}")
                    if response.status in (200, 400):
                        return True
                    else:
                        logger.error(f"[ERROR] / endpoint not available, status: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"[ERROR] Exception checking / endpoint: {e}")
            return False

    def post_battle_log(self, battle_id, message, detail=None, reported_by="battle_royale_orchestrator", api_url="http://localhost:9000"):
        log_entry = {
            "is_result": False,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "reported_by": reported_by,
        }
        if detail:
            log_entry["detail"] = detail
        url = f"{api_url}/battles/{battle_id}"
        try:
            resp = requests.post(url, json=log_entry, timeout=5)
            resp.raise_for_status()
            logger.info(f"Posted log to backend: {message}")
        except Exception as e:
            logger.warning(f"Failed to post log to backend: {e}")

    async def run_full_battle(self):
        """Run the complete battle royale simulation."""
        logger.info("=== Starting Battle Royale Simulation ===")
        
        try:
            # 1. Check prerequisites
            logger.info("Checking prerequisites...")
            green_healthy = await self.check_agent_health(self.green_agent_url)
            if not green_healthy:
                logger.error("Green agent is not healthy")
                return False
            # Check / endpoint
            if not await self.check_a2a_endpoint():
                logger.error("/ endpoint is not available on the green agent. Check the agent process and port.")
                return False
            
            docker_healthy = await self.check_docker_arena()
            if not docker_healthy:
                logger.info("Docker arena not running, starting it...")
                if not await self.start_docker_arena():
                    logger.error("Failed to start Docker arena")
                    return False
            
            # 2. Create battle arena
            if not await self.create_battle_arena():
                logger.error("Failed to create battle arena")
                return False
            
            # 3. Start red agents
            red_agents_started = await self.start_red_agents()
            if not all(red_agents_started):
                logger.warning("Some red agents failed to start")
            
            # 4. Start battle
            if not await self.start_battle():
                logger.error("Failed to start battle")
                return False
            
            # 5. Monitor battle
            monitoring_results = await self.monitor_battle()
            
            # 6. End battle and determine winner
            battle_results = await self.end_battle()
            
            # 7. Generate summary
            summary = {
                "battle_start": datetime.now().isoformat(),
                "duration": self.battle_duration,
                "red_agents_started": red_agents_started,
                "monitoring_data": monitoring_results,
                "battle_results": battle_results
            }
            
            # Save summary to file
            with open("battle_summary.json", "w") as f:
                json.dump(summary, f, indent=2)
            
            logger.info("=== Battle Royale Simulation Complete ===")
            logger.info(f"Summary saved to battle_summary.json")
            
            return True
            
        except Exception as e:
            logger.error(f"Battle simulation failed: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main entry point."""
    orchestrator = BattleOrchestrator()
    success = await orchestrator.run_full_battle()
    
    if success:
        print("Battle royale simulation completed successfully!")
        print("Check battle_summary.json for detailed results.")
    else:
        print("Battle royale simulation failed. Check logs for details.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 