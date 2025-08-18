# -*- coding: utf-8 -*-

import subprocess
import asyncio
import httpx
import platform
import time
import uuid
from datetime import datetime
from fastapi import HTTPException
from typing import Dict, Any, List, Optional
from agentbeats.utils.agents import get_agent_card
from a2a.client import A2ACardResolver
from pathlib import Path

from ..utils.network_utils import get_random_unused_ports
from ..models import AgentCardStatus
from ..db import agent_repo, instance_repo


async def check_launcher_status(launcher_url: str) -> Dict[str, Any]:
    """Check if a launcher URL is accessible and running."""
    try:
            
        launcher_url_clean = launcher_url.rstrip('/')
        
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(f"{launcher_url_clean}/status")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    is_online = data.get("status") == "server up, with agent running"
                except:
                    is_online = False
            else:
                is_online = False
                
        return {
            "online": is_online,
            "status_code": response.status_code,
            "launcher_url": launcher_url_clean
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking launcher status: {str(e)}")
        return {
            "online": False,
            "error": str(e),
            "launcher_url": launcher_url
        }


async def check_agents_liveness(agents: List[Dict[str, Any]], max_concurrent: int = 10) -> List[Dict[str, Any]]:
    """Check liveness for a list of agents and add 'live' field to each agent."""
    async def check_agent_liveness(agent):
        """Check liveness for a single agent."""
        if agent.get("is_hosted"):
            agent["live"] = True  # Hosted agents are always considered live
            return agent

        # Else is remote agent, get tne instance and then get URLs
        agent_id = agent.get("id")
        instance = instance_repo.get_agent_instances_by_agent_id(agent_id)[0]
        agent_url = instance.get("agent_url")
        launcher_url = instance.get("launcher_url")
        
        async def check_agent_card():
            """Check if agent URL is accessible and can return agent card."""
            if not agent_url:
                return False
            try:
                # Use asyncio.wait_for to add additional timeout layer
                agent_card = await asyncio.wait_for(
                    get_agent_card(agent_url), 
                    timeout=1.5
                )
                return bool(agent_card)
            except (asyncio.TimeoutError, Exception):
                return False
        
        async def check_launcher():
            """Check if launcher is alive."""
            if not launcher_url:
                return False
            try:
                # Use asyncio.wait_for to add additional timeout layer
                launcher_status = await asyncio.wait_for(
                    check_launcher_status({"launcher_url": launcher_url}),
                    timeout=1.5
                )
                return launcher_status.get("online", False)
            except (asyncio.TimeoutError, Exception):
                return False
        
        # Run both checks concurrently for this agent
        try:
            agent_card_accessible, launcher_alive = await asyncio.gather(
                check_agent_card(),
                check_launcher(),
                return_exceptions=False
            )
            agent["live"] = agent_card_accessible and launcher_alive
        except Exception:
            agent["live"] = False
        return agent
    
    # Use semaphore to limit concurrent checks
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_with_semaphore(agent):
        async with semaphore:
            return await check_agent_liveness(agent)
    
    # Run all liveness checks with concurrency limit
    checked_agents = await asyncio.gather(
        *[check_with_semaphore(agent) for agent in agents],
        return_exceptions=True
    )
    
    # Handle any exceptions during liveness checks
    for i, result in enumerate(checked_agents):
        if isinstance(result, Exception):
            # If exception, mark agent as not live
            agents[i]["live"] = False
        else:
            agents[i] = result
    
    return agents


async def fetch_agent_card(target_url: str, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """
    Fetch agent card from an A2A compatible agent endpoint.
    
    Example usage:
        card = await fetch_agent_card("https://localhost:8000")
        if card:
            print(f"Agent name: {card.get('name', 'Unknown')}")
    """
    httpx_client = None
    try:
        httpx_client = httpx.AsyncClient(timeout=timeout)
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=target_url)
        
        # Try to get the agent card from the standard A2A endpoint
        card = await resolver.get_agent_card(
            relative_card_path="/.well-known/agent.json"
        )
        
        if card is None:
            return None
            
        # Convert AgentCard object to dictionary
        # AgentCard typically has attributes like name, description, etc.
        card_dict = {
            "name": getattr(card, 'name', None),
            "description": getattr(card, 'description', None),
            "version": getattr(card, 'version', None),
            "author": getattr(card, 'author', None),
            "homepage": getattr(card, 'homepage', None),
            "capabilities": getattr(card, 'capabilities', []),
            "requirements": getattr(card, 'requirements', []),
            "agent_url": target_url,
        }
        
        # Remove None values to keep the dict clean
        card_dict = {k: v for k, v in card_dict.items() if v is not None}
        
        return card_dict
        
    except HTTPException:
        # Re-raise HTTP exceptions to be handled by calling code
        raise
    except Exception as e:
        # Log other exceptions but don't raise them
        print(f"Error fetching agent card from {target_url}: {str(e)}")
        return None
    finally:
        if httpx_client:
            await httpx_client.aclose()


def deploy_hosted_agent(agent_id: str, docker_image_link: str) -> None:
    """
    Deploy an agent instance for a hosted agent using Docker image from Docker Hub.
    This function runs in a background thread and updates agent status.
    Uses docker pull and docker run commands directly.
    
    Args:
        agent_id: The agent ID
        docker_image_link: Docker image name (e.g., 'simonxie2004/tensortrust')
    """
    try:
        print(f"Starting deployment for hosted agent {agent_id} from Docker image {docker_image_link}")
        
        # Generate unique instance ID for this deployment
        instance_id = str(uuid.uuid4())
        
        # Create dockers directory if it doesn't exist
        dockers_dir = Path("dockers")
        dockers_dir.mkdir(exist_ok=True)
        instance_dir = dockers_dir / instance_id
        instance_dir.mkdir(exist_ok=True)
        
        # Generate random ports for this instance
        try:
            agent_port, launcher_port = get_random_unused_ports(count=2)
            print(f"Generated ports for instance {instance_id}: agent_port={agent_port}, launcher_port={launcher_port}")
        except Exception as port_error:
            error_msg = f"Failed to generate random ports: {str(port_error)}"
            print(f"Port generation failed for instance {instance_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        
        # Create log file for docker operations
        log_file_path = instance_dir / "deployment.log"
        
        # First, check if Docker is running
        try:
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                log_file.write(f"=== Docker Deployment Log for Agent Instance {instance_id} ===\n")
                log_file.write(f"Timestamp: {datetime.now().isoformat()}\n")
                log_file.write(f"Agent ID: {agent_id}\n")
                log_file.write(f"Instance ID: {instance_id}\n")
                log_file.write(f"Docker Image: {docker_image_link}\n")
                log_file.write(f"Agent Port: {agent_port}, Launcher Port: {launcher_port}\n")
                log_file.write("=" * 60 + "\n\n")
                log_file.flush()
                
                # Check Docker status
                docker_check = subprocess.run(
                    ["docker", "version"],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30
                )
                
                if docker_check.returncode != 0:
                    error_msg = f"Docker is not running or not accessible. Check logs at: {log_file_path}"
                    print(f"Docker check failed for instance {instance_id}: {error_msg}")
                    update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                    return
                    
                log_file.write(f"\nDocker is running successfully.\n\n")
                print(f"Docker is running for instance {instance_id}")
                
        except Exception as docker_error:
            error_msg = f"Failed to check Docker status: {str(docker_error)}"
            print(f"Docker check failed for instance {instance_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        
        # Step 1: Pull the Docker image
        docker_image_full = f"{docker_image_link}:latest"
        print(f"Pulling Docker image: {docker_image_full}")
        
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"=== Pulling Docker Image ===\n")
                log_file.write(f"Image: {docker_image_full}\n")
                log_file.flush()
                
                pull_result = subprocess.run(
                    ["docker", "pull", docker_image_full],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=600  # 10 minutes timeout for docker pull
                )
                
                if pull_result.returncode != 0:
                    error_msg = f"Docker pull failed for image {docker_image_full}. Check logs at: {log_file_path}"
                    print(f"Docker pull failed for instance {instance_id}: {error_msg}")
                    update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                    return
                    
                log_file.write(f"\nDocker pull completed successfully.\n\n")
                print(f"Successfully pulled Docker image for instance {instance_id}")
                
        except subprocess.TimeoutExpired:
            error_msg = f"Docker pull timeout for image {docker_image_full}. Check logs at: {log_file_path}"
            print(f"Docker pull timeout for instance {instance_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        except Exception as pull_error:
            error_msg = f"Docker pull error: {str(pull_error)}. Check logs at: {log_file_path}"
            print(f"Docker pull failed for instance {instance_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        
        # Step 2: Stop and remove existing container if it exists (by instance_id)
        container_name = f"agent-instance-{instance_id}"
        print(f"Cleaning up existing container: {container_name}")
        
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"=== Cleaning up existing container ===\n")
                log_file.write(f"Container name: {container_name}\n")
                log_file.flush()
                
                # Stop container (ignore errors if not running)
                subprocess.run(
                    ["docker", "stop", container_name],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30
                )
                
                # Remove container (ignore errors if not exists)
                subprocess.run(
                    ["docker", "rm", container_name],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30
                )
                
                log_file.write(f"\nContainer cleanup completed.\n\n")
                
        except Exception as cleanup_error:
            # Log cleanup errors but don't fail the deployment
            print(f"Container cleanup warning for instance {instance_id}: {str(cleanup_error)}")
        
        # Step 3: Run the Docker container
        print(f"Running Docker container for instance {instance_id}")
        
        # Prepare docker run command with volume mounts and port mappings
        docker_run_cmd = [
            "docker", "run",
            "-d",  # Run in detached mode
            "--name", container_name,
            "-p", f"{launcher_port}:9002",  # Map launcher port
            "-p", f"{agent_port}:9003",     # Map agent port
            "-p", "9000:9000",              # Additional port mapping
            "-p", "9001:9001",              # Additional port mapping
            "-e", f"AGENT_PORT=9003",       # Environment variables
            "-e", f"LAUNCHER_PORT=9002",
            "--restart", "unless-stopped",  # Restart policy
            docker_image_full
        ]
        
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"=== Running Docker Container ===\n")
                log_file.write(f"Command: {' '.join(docker_run_cmd)}\n")
                log_file.flush()
                
                run_result = subprocess.run(
                    docker_run_cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=120  # 2 minutes timeout for docker run
                )
                
                if run_result.returncode != 0:
                    error_msg = f"Docker run failed for instance {instance_id}. Check logs at: {log_file_path}"
                    print(f"Docker run failed for instance {instance_id}: {error_msg}")
                    update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                    return
                    
                log_file.write(f"\nDocker container started successfully.\n\n")
                print(f"Successfully started Docker container for instance {instance_id}")
                
        except subprocess.TimeoutExpired:
            error_msg = f"Docker run timeout for instance {instance_id}. Check logs at: {log_file_path}"
            print(f"Docker run timeout for instance {instance_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        except Exception as run_error:
            error_msg = f"Docker run error: {str(run_error)}. Check logs at: {log_file_path}"
            print(f"Docker run failed for instance {instance_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        
        # Step 4: Wait a moment for container to start up
        print(f"Waiting for container to start up...")
        import time
        time.sleep(5)
        
        # Step 5: Try to fetch agent card after deployment
        agent_url = f"http://localhost:{agent_port}"
        launcher_url = f"http://localhost:{launcher_port}"
        print(f"Attempting to fetch agent card from {agent_url}")
        
        try:
            import asyncio
            agent_card = asyncio.run(fetch_agent_card(agent_url, timeout=10.0))
            if agent_card:
                # Add port and container information to agent card
                agent_card['agent_port'] = agent_port
                agent_card['launcher_port'] = launcher_port
                agent_card['container_name'] = container_name
                agent_card['docker_image'] = docker_image_full
                agent_card['instance_id'] = instance_id
                
                # Create agent instance record in database
                try:
                    instance_data = {
                        'agent_id': agent_id,
                        'agent_url': agent_url,
                        'launcher_url': launcher_url,
                        'agent_instance_id': instance_id,
                        'created_at': datetime.utcnow().isoformat() + 'Z',
                        'is_locked': False,
                        'ready': True  # Mark as ready since we successfully fetched agent card
                    }
                    
                    created_instance = instance_repo.create_agent_instance(instance_data)
                    if created_instance:
                        print(f"Successfully created instance record for agent {agent_id}, instance {instance_id}")
                        
                        # Log success
                        with open(log_file_path, 'a', encoding='utf-8') as log_file:
                            log_file.write(f"=== Deployment Successful ===\n")
                            log_file.write(f"Agent URL: {agent_url}\n")
                            log_file.write(f"Launcher URL: {launcher_url}\n")
                            log_file.write(f"Container: {container_name}\n")
                            log_file.write(f"Instance ID: {instance_id}\n")
                            log_file.write(f"Agent card fetched successfully\n")
                        
                        # Update agent status to READY (only if this is the first successful instance)
                        update_agent_deployment_status(agent_id, AgentCardStatus.READY, None, agent_card)
                    else:
                        error_msg = f"Failed to create instance record for agent {agent_id}, instance {instance_id}"
                        print(error_msg)
                        update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                        return
                        
                except Exception as instance_error:
                    error_msg = f"Failed to create instance record: {str(instance_error)}"
                    print(f"Instance creation failed for agent {agent_id}, instance {instance_id}: {error_msg}")
                    update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                    return
            else:
                error_msg = f"Failed to fetch agent card from {agent_url}. Container may be starting. Check logs at: {log_file_path}"
                update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
        except Exception as card_error:
            error_msg = f"Agent card fetch failed: {str(card_error)}. Check logs at: {log_file_path}"
            print(f"Failed to fetch agent card for {agent_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Deployment timeout: {str(e)}"
        print(f"Deployment timeout for agent {agent_id}: {error_msg}")
        update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
    except Exception as e:
        error_msg = f"Deployment error: {str(e)}"
        print(f"Deployment failed for agent {agent_id}: {error_msg}")
        update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)


def update_agent_deployment_status(agent_id: str, status: AgentCardStatus, error_message: str = None, agent_card: dict = None) -> None:
    """
    Update agent deployment status in the database.
    
    Args:
        agent_id: The agent ID
        status: New agent card status
        error_message: Error message if status is ERROR
        agent_card: Agent card data if status is READY
    """
    try:
        agent = agent_repo.get_agent(agent_id)
        if agent:
            agent['agent_card_status'] = status
            if agent_card:
                agent['agent_card'] = agent_card
            elif error_message:
                agent['agent_card'] = {"error": error_message}
            
            agent_repo.update_agent(agent_id, agent)
            print(f"Updated agent {agent_id} status to {status}")
        else:
            print(f"Agent {agent_id} not found for status update")
    except Exception as e:
        print(f"Failed to update agent {agent_id} status: {str(e)}")
    