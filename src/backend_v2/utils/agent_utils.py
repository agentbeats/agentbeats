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

from pathlib import Path as FilePath

from ..utils.network_utils import get_random_unused_ports
from ..models import AgentCardStatus
from ..models.agent_instances import AgentInstanceDockerStatus
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

        return card.model_dump()
        
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


def deploy_hosted_agent_instance(agent_id: str, docker_image_link: str, agent_instance_id: str, agent_port: int, launcher_port: int, created_at: str) -> None:
    """
    Deploy an agent instance for a hosted agent using Docker image from Docker Hub.
    This function runs in a background thread and updates agent status.
    Uses docker pull and docker run commands directly.
    
    Note: The agent instance record should already exist in the database before calling this function.
    This function will only update the docker_status and agent_card.
    
    Args:
        agent_id: The agent ID
        docker_image_link: Docker image name (e.g., 'simonxie2004/tensortrust')
        agent_instance_id: The unique instance ID for this deployment (should already exist in DB)
        agent_port: The port for the agent service
        launcher_port: The port for the launcher service
        created_at: The creation timestamp in ISO format
    """
    try:
        print(f"Starting deployment for hosted agent {agent_id} from Docker image {docker_image_link}")
        
        # Use provided instance ID
        instance_id = agent_instance_id
        
        # Create dockers directory if it doesn't exist
        dockers_dir = FilePath("dockers")
        dockers_dir.mkdir(exist_ok=True)
        instance_dir = dockers_dir / instance_id
        instance_dir.mkdir(exist_ok=True)
        
        # Use provided ports
        print(f"Using provided ports for instance {instance_id}: agent_port={agent_port}, launcher_port={launcher_port}")
        
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
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30,
                    encoding='utf-8'
                )
                
                # Write output to log file
                log_file.write(docker_check.stdout or "")
                log_file.flush()
                
                if docker_check.returncode != 0:
                    error_msg = f"Docker is not running or not accessible. Check logs at: {log_file_path}"
                    print(f"Docker check failed for instance {instance_id}: {error_msg}")
                    update_instance_docker_status(instance_id, AgentInstanceDockerStatus.STOPPED)
                    update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                    return
                    
                log_file.write(f"\nDocker is running successfully.\n\n")
                print(f"Docker is running for instance {instance_id}")
                
        except Exception as docker_error:
            error_msg = f"Failed to check Docker status: {str(docker_error)}"
            print(f"Docker check failed for instance {instance_id}: {error_msg}")
            update_instance_docker_status(instance_id, AgentInstanceDockerStatus.STOPPED)
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
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=600,  # 10 minutes timeout for docker pull
                    encoding='utf-8'
                )
                
                # Write output to log file
                log_file.write(pull_result.stdout or "")
                log_file.flush()
                
                if pull_result.returncode != 0:
                    error_msg = f"Docker pull failed for image {docker_image_full}. Check logs at: {log_file_path}"
                    print(f"Docker pull failed for instance {instance_id}: {error_msg}")
                    update_instance_docker_status(instance_id, AgentInstanceDockerStatus.STOPPED)
                    update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                    return
                    
                log_file.write(f"\nDocker pull completed successfully.\n\n")
                print(f"Successfully pulled Docker image for instance {instance_id}")
                
        except subprocess.TimeoutExpired:
            error_msg = f"Docker pull timeout for image {docker_image_full}. Check logs at: {log_file_path}"
            print(f"Docker pull timeout for instance {instance_id}: {error_msg}")
            update_instance_docker_status(instance_id, AgentInstanceDockerStatus.STOPPED)
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        except Exception as pull_error:
            error_msg = f"Docker pull error: {str(pull_error)}. Check logs at: {log_file_path}"
            print(f"Docker pull failed for instance {instance_id}: {error_msg}")
            update_instance_docker_status(instance_id, AgentInstanceDockerStatus.STOPPED)
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        
        # Step 2: Run the Docker container
        container_name = f"agent-instance-{instance_id}"
        print(f"Running Docker container for instance {instance_id}")
        
        # Prepare docker run command with volume mounts and port mappings
        docker_run_cmd = [
            "docker", "run",
            "-d",  # Run in detached mode
            "--name", container_name,
            "-e", r"OPENAI_API_KEY=${OPENAI_API_KEY}", # TODO: use user upload env vars
            "-p", f"{launcher_port}:9002",  # Map launcher port
            "-p", f"{agent_port}:9003",     # Map agent port
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
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=120,  # 2 minutes timeout for docker run
                    encoding='utf-8'
                )
                
                # Write output to log file
                log_file.write(run_result.stdout or "")
                log_file.flush()
                
                if run_result.returncode != 0:
                    error_msg = f"Docker run failed for instance {instance_id}. Check logs at: {log_file_path}"
                    print(f"Docker run failed for instance {instance_id}: {error_msg}")
                    update_instance_docker_status(instance_id, AgentInstanceDockerStatus.STOPPED)
                    update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
                    return
                    
                log_file.write(f"\nDocker container started successfully.\n\n")
                print(f"Successfully started Docker container for instance {instance_id}")
                
                # Update docker status to running
                update_instance_docker_status(instance_id, AgentInstanceDockerStatus.RUNNING)
                
        except subprocess.TimeoutExpired:
            error_msg = f"Docker run timeout for instance {instance_id}. Check logs at: {log_file_path}"
            print(f"Docker run timeout for instance {instance_id}: {error_msg}")
            update_instance_docker_status(instance_id, AgentInstanceDockerStatus.STOPPED)
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        except Exception as run_error:
            error_msg = f"Docker run error: {str(run_error)}. Check logs at: {log_file_path}"
            print(f"Docker run failed for instance {instance_id}: {error_msg}")
            update_instance_docker_status(instance_id, AgentInstanceDockerStatus.STOPPED)
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
            return
        
        # Step 3: Wait for container to start up and try to fetch agent card
        time.sleep(5)
        agent_url = f"http://localhost:{agent_port}"
        launcher_url = f"http://localhost:{launcher_port}"
        print(f"Waiting for container to start up and attempting to fetch agent card from {agent_url}")
        
        agent_card = None
        max_attempts = 10
        
        for attempt in range(1, max_attempts + 1):
            print(f"Attempt {attempt}/{max_attempts}: Fetching agent card from {agent_url}")
            
            try:
                agent_card = asyncio.run(fetch_agent_card(agent_url, timeout=5.0))
                if agent_card:
                    print(f"Successfully fetched agent card on attempt {attempt}")
                    break
                else:
                    print(f"Agent card fetch returned None on attempt {attempt}")
            except Exception as card_error:
                print(f"Agent card fetch failed on attempt {attempt}: {str(card_error)}")
            
            if attempt < max_attempts:
                print(f"Waiting 1 second before next attempt...")
                time.sleep(1)
        
        # Step 4: Process the result
        if agent_card:
            # Update instance docker status and agent card (instance should already exist)
            try:
                print(f"Successfully deployed agent {agent_id}, instance {instance_id}")
                
                # Log success
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"=== Deployment Successful ===\n")
                    log_file.write(f"Agent URL: {agent_url}\n")
                    log_file.write(f"Launcher URL: {launcher_url}\n")
                    log_file.write(f"Container: {container_name}\n")
                    log_file.write(f"Instance ID: {instance_id}\n")
                    log_file.write(f"Agent card fetched successfully\n")
                
                # Update agent status to READY with agent card (keeping original card data)
                update_agent_deployment_status(agent_id, AgentCardStatus.READY, None, agent_card)
                    
            except Exception as instance_error:
                error_msg = f"Failed to update deployment status: {str(instance_error)}"
                print(f"Status update failed for agent {agent_id}, instance {instance_id}: {error_msg}")
                update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
        else:
            # Agent card fetch failed after all attempts
            error_msg = f"Instance deployment timeout: Failed to fetch agent card from {agent_url} after {max_attempts} attempts. Container may have failed to start properly. Check logs at: {log_file_path}"
            print(f"Failed to fetch agent card for {agent_id} after {max_attempts} attempts")
            
            # Log the timeout error
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"=== Deployment Timeout ===\n")
                log_file.write(f"Failed to fetch agent card after {max_attempts} attempts\n")
                log_file.write(f"Agent URL: {agent_url}\n")
                log_file.write(f"Container: {container_name}\n")
                log_file.write(f"Instance ID: {instance_id}\n")
            
            # Container is running but agent is not accessible
            update_instance_docker_status(instance_id, AgentInstanceDockerStatus.RUNNING)
            update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Deployment timeout: {str(e)}"
        print(f"Deployment timeout for agent {agent_id}: {error_msg}")
        update_instance_docker_status(agent_instance_id, AgentInstanceDockerStatus.STOPPED)
        update_agent_deployment_status(agent_id, AgentCardStatus.ERROR, error_msg)
    except Exception as e:
        error_msg = f"Deployment error: {str(e)}"
        print(f"Deployment failed for agent {agent_id}: {error_msg}")
        update_instance_docker_status(agent_instance_id, AgentInstanceDockerStatus.STOPPED)
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


def update_instance_docker_status(agent_instance_id: str, docker_status: AgentInstanceDockerStatus) -> None:
    """
    Update agent instance docker status in the database.
    
    Args:
        agent_instance_id: The agent instance ID
        docker_status: New docker status
    """
    try:
        instance_repo.update_agent_instance(agent_instance_id, {'docker_status': docker_status})
        print(f"Updated instance {agent_instance_id} docker status to {docker_status}")
    except Exception as e:
        print(f"Failed to update instance {agent_instance_id} docker status: {str(e)}")


def stop_hosted_agent_instance(agent_instance_id: str) -> None:
    """
    Stop and remove a hosted agent instance Docker container.
    This function runs in a background thread and updates the database status.
    
    Args:
        agent_instance_id: The agent instance ID
    """
    try:
        print(f"Starting Docker container stop process for instance {agent_instance_id}")
        
        container_name = f"agent-instance-{agent_instance_id}"
        
        # Create dockers directory path for logging
        dockers_dir = FilePath("dockers")
        instance_dir = dockers_dir / agent_instance_id
        
        # Create log file for stop operations
        log_file_path = None
        if instance_dir.exists():
            log_file_path = instance_dir / "stop.log"
        
        # Step 1: Stop the container
        try:
            if log_file_path:
                with open(log_file_path, 'w', encoding='utf-8') as log_file:
                    log_file.write(f"=== Docker Container Stop Log for Instance {agent_instance_id} ===\n")
                    log_file.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    log_file.write(f"Container Name: {container_name}\n")
                    log_file.write("=" * 60 + "\n\n")
                    log_file.flush()
            
            print(f"Stopping Docker container: {container_name}")
            
            # Stop the container
            stop_result = subprocess.run(
                ["docker", "stop", container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30,  # 30 seconds timeout for stop
                encoding='utf-8'
            )
            
            if log_file_path:
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"=== Stopping Container ===\n")
                    log_file.write(f"Command: docker stop {container_name}\n")
                    log_file.write(stop_result.stdout or "")
                    log_file.write(f"Return code: {stop_result.returncode}\n\n")
                    log_file.flush()
            
            if stop_result.returncode != 0:
                print(f"Docker stop failed for container {container_name}: {stop_result.stdout}")
                if "No such container" in (stop_result.stdout or ""):
                    print(f"Container {container_name} was already removed")
                else:
                    # Don't return here, continue to try removal
                    print(f"Stop failed but continuing to removal step")
            else:
                print(f"Successfully stopped Docker container {container_name}")
                
        except subprocess.TimeoutExpired:
            print(f"Docker stop timeout for container {container_name}, forcing removal")
            if log_file_path:
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"Stop operation timed out, proceeding to force removal\n\n")
        except Exception as stop_error:
            print(f"Docker stop error for container {container_name}: {str(stop_error)}")
            if log_file_path:
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"Stop error: {str(stop_error)}\n\n")
        
        # Step 2: Remove the container
        try:
            print(f"Removing Docker container: {container_name}")
            
            # Remove the container (force remove if necessary)
            remove_result = subprocess.run(
                ["docker", "rm", "-f", container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30,  # 30 seconds timeout for remove
                encoding='utf-8'
            )
            
            if log_file_path:
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"=== Removing Container ===\n")
                    log_file.write(f"Command: docker rm -f {container_name}\n")
                    log_file.write(remove_result.stdout or "")
                    log_file.write(f"Return code: {remove_result.returncode}\n\n")
                    log_file.flush()
            
            if remove_result.returncode != 0:
                print(f"Docker remove failed for container {container_name}: {remove_result.stdout}")
                if "No such container" in (remove_result.stdout or ""):
                    print(f"Container {container_name} was already removed")
                    # This is actually success
                    remove_success = True
                else:
                    remove_success = False
            else:
                print(f"Successfully removed Docker container {container_name}")
                remove_success = True
                
        except subprocess.TimeoutExpired:
            print(f"Docker remove timeout for container {container_name}")
            remove_success = False
            if log_file_path:
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"Remove operation timed out\n\n")
        except Exception as remove_error:
            print(f"Docker remove error for container {container_name}: {str(remove_error)}")
            remove_success = False
            if log_file_path:
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"Remove error: {str(remove_error)}\n\n")
        
        # Step 3: Update database status and clean up
        if remove_success:
            # Update status to STOPPED and delete instance record
            update_instance_docker_status(agent_instance_id, AgentInstanceDockerStatus.STOPPED)
            
            # Delete the instance from database
            try:
                instance_repo.delete_agent_instance(agent_instance_id)
                print(f"Successfully deleted instance record for {agent_instance_id}")
                
                if log_file_path:
                    with open(log_file_path, 'a', encoding='utf-8') as log_file:
                        log_file.write(f"=== Cleanup Successful ===\n")
                        log_file.write(f"Instance record deleted from database\n")
                        log_file.write(f"Container removed successfully\n")
                
            except Exception as db_error:
                print(f"Failed to delete instance record for {agent_instance_id}: {str(db_error)}")
                if log_file_path:
                    with open(log_file_path, 'a', encoding='utf-8') as log_file:
                        log_file.write(f"Database cleanup error: {str(db_error)}\n")
        else:
            # Keep status as STOPPING if removal failed
            print(f"Docker container removal failed for {agent_instance_id}, keeping status as STOPPING")
            if log_file_path:
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"=== Cleanup Failed ===\n")
                    log_file.write(f"Container removal failed, status remains STOPPING\n")
        
    except Exception as e:
        print(f"Failed to stop hosted agent instance {agent_instance_id}: {str(e)}")
        # Keep status as STOPPING
        print(f"Keeping instance {agent_instance_id} status as STOPPING due to error")


def read_file_log(agent_instance_id: str, log_type: str) -> tuple[str, bool]:
    """
    Read file-based logs for an agent instance.
    
    Args:
        agent_instance_id: The agent instance ID
        log_type: Type of log to read ('deployment' or 'stop')
    
    Returns:
        tuple: (log_content, log_exists)
    
    Raises:
        HTTPException: If there's an error reading the log file
    """
    try:
        # Validate log type
        if log_type not in ['deployment', 'stop']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid log type '{log_type}'. Must be 'deployment' or 'stop'."
            )
        
        # Create dockers directory path
        dockers_dir = FilePath("dockers")
        instance_dir = dockers_dir / agent_instance_id
        log_file_path = instance_dir / f"{log_type}.log"
        
        # Check if log file exists and read content
        log_exists = log_file_path.exists()
        log_content = ""
        
        if log_exists:
            try:
                with open(log_file_path, 'r', encoding='utf-8') as log_file:
                    log_content = log_file.read()
            except Exception as read_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to read {log_type} log: {str(read_error)}"
                )
        else:
            if log_type == 'deployment':
                log_content = "Deployment log not found. The agent instance may not have been deployed yet or the log file was deleted."
            elif log_type == 'stop':
                log_content = "Stop log not found. The agent instance may not have been stopped yet or the log file was deleted."
        
        return log_content, log_exists
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading {log_type} log: {str(e)}"
        )


def read_live_docker_log(agent_instance_id: str, lines: int = 100) -> tuple[str, bool, str]:
    """
    Read live Docker logs for a hosted agent instance.
    
    Args:
        agent_instance_id: The agent instance ID
        lines: Number of lines to fetch from the end
    
    Returns:
        tuple: (log_content, container_exists, container_name)
    
    Raises:
        HTTPException: If there's an error executing Docker commands
    """
    try:
        # Construct the container name
        container_name = f"agent-instance-{agent_instance_id}"
        
        # Check if Docker container exists and get logs
        container_exists = False
        log_content = ""
        
        try:
            # First check if container exists
            check_result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8'
            )
            
            if check_result.returncode == 0:
                container_exists = True
                
                # Get Docker logs
                logs_result = subprocess.run(
                    ["docker", "logs", "--tail", str(lines), container_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding='utf-8'
                )
                
                if logs_result.returncode == 0:
                    log_content = logs_result.stdout or ""
                    if logs_result.stderr:
                        log_content += "\n--- STDERR ---\n" + logs_result.stderr
                else:
                    log_content = f"Failed to retrieve Docker logs: {logs_result.stderr}"
            else:
                log_content = f"Docker container '{container_name}' not found. The agent instance may not be deployed or the container was removed."
                
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=500,
                detail="Docker command timeout. Please try again."
            )
        except Exception as docker_error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to execute Docker command: {str(docker_error)}"
            )
        
        return log_content, container_exists, container_name
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving live Docker logs: {str(e)}"
        )
    