# -*- coding: utf-8 -*-

import subprocess
import asyncio
import httpx
import platform
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


def deploy_hosted_agent(agent_id: str, github_link: str) -> None:
    """
    Deploy a hosted agent by cloning GitHub repo and running docker compose.
    This function runs in a background thread and updates agent status.
    
    Args:
        agent_id: The agent ID
        github_link: GitHub repository URL to clone
    """
    try:
        print(f"Starting deployment for hosted agent {agent_id} from {github_link}")
        
        # Create dockers directory if it doesn't exist
        dockers_dir = Path("dockers")
        dockers_dir.mkdir(exist_ok=True)
        
        # Agent directory path
        agent_dir = dockers_dir / agent_id
        
        # Remove existing directory if it exists
        if agent_dir.exists():
            import shutil
            shutil.rmtree(agent_dir)
            print(f"Removed existing directory: {agent_dir}")
        
        # Clone the repository directly to dockers/{agent_id}
        print(f"Cloning {github_link} to {agent_dir}")
        clone_result = subprocess.run(
            ["git", "clone", github_link, str(agent_dir)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for git clone
        )
        
        if clone_result.returncode != 0:
            print(f"Git clone failed for agent {agent_id}: {clone_result.stderr}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, f"Git clone failed: {clone_result.stderr}")
            return
            
        print(f"Successfully cloned repository for agent {agent_id}")
        
        # Generate random ports for the agent
        try:
            agent_port, launcher_port = get_random_unused_ports(count=2)
            print(f"Generated ports for agent {agent_id}: agent_port={agent_port}, launcher_port={launcher_port}")
        except Exception as port_error:
            error_msg = f"Failed to generate random ports: {str(port_error)}"
            print(f"Port generation failed for agent {agent_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        
        # Check if docker-compose.yml exists
        compose_file_path = agent_dir / "docker-compose.yml"
        if not compose_file_path.exists():
            # Also check for docker-compose.yaml (alternative naming)
            compose_file_alt_path = agent_dir / "docker-compose.yaml"
            if not compose_file_alt_path.exists():
                error_msg = f"docker-compose.yml or docker-compose.yaml not found in {agent_dir}"
                print(f"Deployment failed for agent {agent_id}: {error_msg}")
                update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                return
            
        # Prepare docker compose command based on operating system
        print(f"Running docker compose for agent {agent_id} in {agent_dir}")
        
        # First, check if Docker is running
        try:
            docker_check = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if docker_check.returncode != 0:
                error_msg = f"Docker is not running or not accessible: {docker_check.stderr}"
                print(f"Docker check failed for agent {agent_id}: {error_msg}")
                update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                return
            print(f"Docker is running for agent {agent_id}")
        except Exception as docker_error:
            error_msg = f"Failed to check Docker status: {str(docker_error)}"
            print(f"Docker check failed for agent {agent_id}: {error_msg}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        
        if platform.system().lower() == "windows":
            # Windows PowerShell command
            compose_cmd = [
                "powershell", "-Command",
                f"$env:HOST_AGENT_PORT={agent_port}; $env:HOST_LAUNCHER_PORT={launcher_port}; docker compose up -d --build"
            ]
        else:
            # Linux/Unix command
            compose_cmd = ["docker", "compose", "up", "-d", "--build"]
            compose_env = {
                **subprocess.os.environ,  # Copy existing environment
                "HOST_AGENT_PORT": str(agent_port),
                "HOST_LAUNCHER_PORT": str(launcher_port)
            }
        
        # Execute docker compose with appropriate environment variables
        if platform.system().lower() == "windows":
            compose_result = subprocess.run(
                compose_cmd,
                cwd=str(agent_dir),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout for docker build
            )
        else:
            compose_result = subprocess.run(
                compose_cmd,
                cwd=str(agent_dir),
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout for docker build
                env=compose_env
            )
        
        if compose_result.returncode != 0:
            print(f"Docker compose failed for agent {agent_id}: {compose_result.stderr}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, f"Docker compose failed: {compose_result.stderr}")
            return
            
        print(f"Successfully deployed hosted agent {agent_id}")
        
        # Try to fetch agent card after deployment using the generated agent port
        agent_url = f"http://localhost:{agent_port}"
        launcher_url = f"http://localhost:{launcher_port}"
        print(f"Attempting to fetch agent card from {agent_url}")
        
        try:
            import asyncio
            agent_card = asyncio.run(fetch_agent_card(agent_url, timeout=10.0))
            if agent_card:
                # Add port information to agent card
                agent_card['agent_port'] = agent_port
                agent_card['launcher_port'] = launcher_port
                
                # Create agent instance record in database
                try:
                    from datetime import datetime
                    import uuid
                    
                    instance_data = {
                        'agent_id': agent_id,
                        'agent_url': agent_url,
                        'launcher_url': launcher_url,
                        'agent_instance_id': str(uuid.uuid4()),
                        'created_at': datetime.utcnow().isoformat() + 'Z',
                        'is_locked': False,
                        'ready': True  # Mark as ready since we successfully fetched agent card
                    }
                    
                    created_instance = instance_repo.create_agent_instance(instance_data)
                    if created_instance:
                        print(f"Successfully created instance record for hosted agent {agent_id}")
                        # Add instance info to agent card
                        agent_card['instance_id'] = created_instance['agent_instance_id']
                    else:
                        print(f"Warning: Failed to create instance record for agent {agent_id}, but agent is running")
                        
                except Exception as instance_error:
                    print(f"Warning: Failed to create instance record for agent {agent_id}: {str(instance_error)}")
                    # Don't fail the entire deployment just because instance creation failed
                
                update_agent_deployment_status(agent_id, AgentCardStatus.READY, None, agent_card)
            else:
                update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, f"Failed to fetch agent card from {agent_url}")
        except Exception as card_error:
            print(f"Failed to fetch agent card for {agent_id}: {str(card_error)}")
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, f"Agent card fetch failed: {str(card_error)}")
        
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
