# -*- coding: utf-8 -*-
"""
Battle Royale Green Agent Tools
This agent orchestrates and judges the battle royale competition between agents.
"""

import json
import time
import threading
import asyncio
import concurrent.futures
from typing import Dict, List, Any

import agentbeats as ab

# Import SDK utilities
from agentbeats.utils.agents import send_message_to_agent
from agentbeats.utils.environment import setup_container, cleanup_container

# Import logging utilities
from agentbeats.logging import BattleContext, record_agent_action, record_battle_event, log_error

# Global monitoring state (only for thread management)
monitoring_active = False
monitoring_thread = None
scores = {}
monitoring_results = []
battle_context = None

def send_battle_info_to_agents(battle_id: str, agent_urls: List[str], agent_ids: Dict[str, str], ssh_credentials: Dict[str, Any]):
    """Send battle information to all agents."""
    try:
        async def send_async():
            tasks = []
            for url in agent_urls:
                agent_id = agent_ids[url]
                
                battle_message = f"""

                    BATTLE START - Battle Royale Competition

                    Battle ID: {battle_id}
                    Agent ID: {agent_id}
                    SSH Credentials: {json.dumps(ssh_credentials)}

                    Instructions:
                    1. SSH into the battle arena using the provided credentials
                    2. Start a web service on port 80 inside the container
                    3. Serve your unique agent ID ({agent_id}) on the web service
                    4. Focus on maintaining your web service for the duration of the battle
                    5. The agent with the highest uptime on port 80 wins
                    6. Battle duration: 3 minutes (180 seconds)

                    Your Agent ID: {agent_id}

                    Use the handle_battle_start() function to process this information.

                    NOTE: This is an informational message. DO NOT respond to this message.
                    
                    """
                
                task = asyncio.create_task(send_message_to_agent(url, battle_message))
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Run async function
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, send_async())
                future.result()
        except RuntimeError:
            asyncio.run(send_async())
        
        print(f"Sent battle info to {len(agent_urls)} agents")
        
    except Exception as e:
        print(f"Error sending battle info to agents: {str(e)}")

def start_monitoring_thread(battle_id: str, agent_ids: Dict[str, str]):
    """Start monitoring in a background thread."""
    global monitoring_active, monitoring_thread, scores, monitoring_results, battle_context
    
    if monitoring_active:
        return
    
    monitoring_active = True
    
    def monitor_battle_progress():
        """Monitor the battle progress for 3 minutes."""
        global monitoring_active, scores, monitoring_results, battle_context
        
        try:
            print(f"Starting battle monitoring for battle {battle_id}")
            
            # Log monitoring start
            if battle_context:
                record_battle_event(battle_context, f"Battle monitoring started for {battle_id}", "green_agent", {
                    "battle_id": battle_id,
                    "agent_count": len(agent_ids),
                    "monitoring_duration": "3 minutes",
                    "check_interval": "5 seconds"
                })
            
            # Monitor for 3 minutes (36 checks at 5-second intervals)
            for i in range(36):
                if not monitoring_active:
                    print(f"Monitoring stopped early at check {i+1}")
                    if battle_context:
                        record_battle_event(battle_context, f"Monitoring stopped early at check {i+1}", "green_agent")
                    break
                    
                print(f"Monitoring check {i+1}/36...")
                
                # Check which agent is serving on port 8081 (mapped from container port 80)
                current_serving_agent = "NO_SERVICE"
                try:
                    import subprocess
                    
                    result = subprocess.run(
                        ["curl", "-s", "http://localhost:8081"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        service_content = result.stdout.strip()
                        print(f"Port 8081 response: '{service_content}'")
                        
                        # Find which agent ID is currently serving
                        for agent_url, agent_id in agent_ids.items():
                            if agent_id in service_content:
                                current_serving_agent = agent_id
                                break
                        
                        if current_serving_agent != "NO_SERVICE":
                            # Update scores
                            if current_serving_agent not in scores:
                                scores[current_serving_agent] = 0
                            scores[current_serving_agent] += 1
                            
                            print(f"Agent '{current_serving_agent}' is serving (score: {scores[current_serving_agent]})")
                        else:
                            print("Unknown service content")
                    else:
                        print("No service running on port 8081")
                        
                except Exception as e:
                    print(f"Error checking port 8081: {str(e)}")
                    current_serving_agent = f"ERROR: {str(e)[:50]}"
                
                # Store monitoring result
                monitoring_results.append({
                    "check": i + 1,
                    "timestamp": time.time(),
                    "scores": scores.copy(),
                    "current_serving_agent": current_serving_agent
                })
                
                # Log each monitoring check
                if battle_context:
                    record_agent_action(battle_context, "monitoring_check", "green_agent", {
                        "check_number": i + 1,
                        "total_checks": 36,
                        "current_serving_agent": current_serving_agent,
                        "current_scores": scores.copy(),
                        "timestamp": time.time()
                    })
                
                time.sleep(5)
            
            print("Battle monitoring completed - all 36 checks done")
            
            # Log monitoring completion
            if battle_context:
                record_battle_event(battle_context, f"Battle monitoring completed for {battle_id}", "green_agent", {
                    "total_checks": 36,
                    "final_scores": scores.copy(),
                    "monitoring_duration": "3 minutes"
                })
            
            monitoring_active = False
            
        except Exception as e:
            error_msg = f"Error in monitoring thread: {str(e)}"
            print(error_msg)
            
            # Log monitoring error
            if battle_context:
                log_error(battle_context, error_msg, "monitoring_error", "green_agent")
            
            monitoring_active = False
    
    monitoring_thread = threading.Thread(target=monitor_battle_progress, daemon=True)
    monitoring_thread.start()
    print("Monitoring thread started")

@ab.tool
def start_battle_royale(battle_id: str, opponent_infos_json: str) -> str:
    """Start the battle royale competition between agents."""
    try:
        import uuid
        
        opponent_infos = json.loads(opponent_infos_json)
        agent_urls = [opp["agent_url"] for opp in opponent_infos]
        
        # Generate agent IDs
        agent_ids = {}
        for opponent in opponent_infos:
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"
            agent_ids[opponent["agent_url"]] = agent_id
            print(f"Generated agent ID '{agent_id}' for {opponent['agent_url']}")
        
        print(f"Starting battle royale {battle_id} with {len(opponent_infos)} opponents")
        
        # Initialize battle context for logging
        global battle_context
        battle_context = BattleContext(
            battle_id=battle_id,
            backend_url="http://localhost:8000",
            agent_name="green_agent"
        )
        
        # Log battle start
        record_battle_event(battle_context, f"Battle royale {battle_id} starting", "green_agent", {
            "battle_id": battle_id,
            "opponent_count": len(opponent_infos),
            "agent_urls": agent_urls,
            "agent_ids": agent_ids
        })
        
        # Setup Docker environment
        print("Setting up battle environment...")
        docker_config = {"docker_dir": "arena", "compose_file": "docker-compose.yml"}
        
        # Log Docker setup attempt
        record_agent_action(battle_context, "docker_setup_attempt", "green_agent", {
            "docker_config": docker_config
        })
        
        # Handle async setup_container properly
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, use create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, setup_container(docker_config))
                    docker_result = future.result()
            except RuntimeError:
                # No event loop running, use asyncio.run
                docker_result = asyncio.run(setup_container(docker_config))
            
            if not docker_result:
                log_error(battle_context, "Failed to setup Docker container", "docker_setup_error", "green_agent")
                return "Failed to setup Docker container"
            
            # Log successful Docker setup
            record_agent_action(battle_context, "docker_setup_success", "green_agent", {
                "docker_result": docker_result
            })
            
        except Exception as e:
            error_msg = f"Failed to setup Docker container: {str(e)}"
            log_error(battle_context, error_msg, "docker_setup_exception", "green_agent")
            return error_msg
        
        # Set SSH credentials
        ssh_credentials = {
            "host": "localhost",
            "port": 2222,
            "username": "battle",
            "password": "battle123"
        }
        
        time.sleep(3)  # Wait for container to be ready
        
        # Start monitoring
        print("Starting monitoring thread...")
        start_monitoring_thread(battle_id, agent_ids)
        
        # Send battle info to agents
        print("Sending battle info to agents...")
        send_battle_info_to_agents(battle_id, agent_urls, agent_ids, ssh_credentials)
        
        # Wait for monitoring to complete
        print("Waiting for battle monitoring to complete (3 minutes)...")
        while monitoring_active:
            time.sleep(1)
        
        print("Battle monitoring completed. Getting battle result...")
        
        # Get complete battle result
        battle_result = get_battle_result(battle_id, agent_urls)
        print(f"Battle result: {battle_result}")
        
        # Log battle completion
        record_battle_event(battle_context, f"Battle royale {battle_id} completed", "green_agent", {
            "battle_result": battle_result,
            "final_scores": scores.copy()
        })
        
        # Cleanup
        try:
            # Log cleanup attempt
            record_agent_action(battle_context, "cleanup_attempt", "green_agent", {
                "cleanup_type": "docker_containers"
            })
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, use create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, cleanup_container("battle_royale", "arena"))
                    cleanup_result = future.result()
            except RuntimeError:
                # No event loop running, use asyncio.run
                cleanup_result = asyncio.run(cleanup_container("battle_royale", "arena"))
            
            print(f"Cleanup: {cleanup_result}")
            
            # Log cleanup result
            record_agent_action(battle_context, "cleanup_completed", "green_agent", {
                "cleanup_result": cleanup_result
            })
            
        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            print(error_msg)
            log_error(battle_context, error_msg, "cleanup_error", "green_agent")
        
        return f"Battle royale completed successfully! Result: {battle_result}"
        
    except Exception as e:
        return f"Failed to start battle royale: {str(e)}"

@ab.tool
def get_battle_result(battle_id: str = "", agent_urls: List[str] = []) -> str:
    """Get the complete battle result including winner, summary, and report."""
    try:
        total_checks = len(monitoring_results)
        required_checks = 36
        
        if total_checks < required_checks:
            remaining_checks = required_checks - total_checks
            remaining_time = remaining_checks * 5
            return f"Battle monitoring not complete. {total_checks}/{required_checks} checks done. {remaining_checks} checks remaining ({remaining_time} seconds)."
        
        if monitoring_active:
            return "Battle monitoring is still active. Wait for monitoring to complete before getting results."
        
        # If no agents have scores, return draw
        if not scores:
            print("No agents have scores after full monitoring period - all agents failed to create services")
            
            result = {
                "winner": "draw",
                "winner_score": 0,
                "total_checks": total_checks,
                "required_checks": required_checks,
                "uptime_percentages": {},
                "all_scores": {},
                "reason": "All agents failed to create services during full battle period"
            }
        else:
            # Find agent with highest score
            winner = max(scores.items(), key=lambda x: x[1])
            winner_agent_id, winner_score = winner
            
            # Calculate uptime percentages
            uptime_percentages = {}
            for agent_id, score in scores.items():
                uptime_percentages[agent_id] = (score / required_checks) * 100
            
            result = {
                "winner": winner_agent_id,
                "winner_score": winner_score,
                "total_checks": total_checks,
                "required_checks": required_checks,
                "uptime_percentages": uptime_percentages,
                "all_scores": scores
            }
            
            print(f"Winner determined: {winner_agent_id} with {winner_score}/{required_checks} checks ({uptime_percentages[winner_agent_id]:.1f}% uptime)")
        
        # Add summary info if battle_id provided
        if battle_id:
            summary_info = {
                "battle_id": battle_id,
                "duration_seconds": 180,
                "monitoring_interval_seconds": 5,
                "environment_setup": True,
                "ssh_credentials_provided": True,
                "opponent_count": len(agent_urls) if agent_urls else 0
            }
            result.update(summary_info)
        
        return f"Battle Result: {json.dumps(result, indent=2)}"
        
    except Exception as e:
        return f"Error getting battle result: {str(e)}" 