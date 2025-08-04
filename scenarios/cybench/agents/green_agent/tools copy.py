#!/usr/bin/env python3
"""
This file contains the tools for the green agent to interact with the cybench task.

Available tools:
- setup_cybench_task: Setup the cybench task by starting the cybench server and generating the task.
- execute_command_in_container: Execute a command in the running container and return the output.
- destroy_container: Destroy the container and optionally remove the network.
"""

import os
import sys
import json
import subprocess
import docker
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from agentbeats import tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


client = docker.from_env()
image_name = "cybench/cybench:latest"
network_name = "shared_net"
containers = {}  # Maps container_name to container object


def validate_current_directory():
    """Validate that we're running from the cybench directory"""
    current_dir = Path.cwd().name
    if current_dir != "cybench":
        raise ValueError(
            "Error: Please run this script from the cybench directory."
        )


def cleanup_existing_container(battle_id: str = None):
    """Remove existing container if it exists"""
    container_name = _get_container_name(battle_id)
    try:
        container = client.containers.get(container_name)
        container.remove(force=True)
        logger.info(f"Removed existing container: {container_name}")
        if container_name in containers:
            del containers[container_name]
    except docker.errors.NotFound:
        pass  # Container doesn't exist, which is fine


def create_network_if_needed():
    """Create shared network if it doesn't exist"""
    try:
        client.networks.get(network_name)
    except docker.errors.NotFound:
        logger.info(f"Creating Docker network: {network_name}")
        client.networks.create(network_name)


def execute_task_script(script_path: str, script_name: str):
    """Execute start_docker.sh or stop_docker.sh if they exist"""
    if os.path.isfile(script_path):
        logger.info(f"Executing {script_name} script for the task")
        try:
            subprocess.run([script_path], check=True, shell=True)
        except subprocess.CalledProcessError as e:
            logger.warning(
                f"Warning: {script_name} script failed with exit code {e.returncode}"
            )


def parse_json_output(output: str) -> Optional[Dict[Any, Any]]:
    """Parse JSON output from the container logs"""
    lines = output.split("\n")
    json_start = False
    json_lines = []

    for line in lines:
        if "--- JSON OUTPUT ---" in line:
            json_start = True
            continue
        elif "--- END JSON OUTPUT ---" in line:
            break
        elif json_start:
            json_lines.append(line)

    if json_lines:
        try:
            json_content = "\n".join(json_lines)
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.warning(f"Warning: Failed to parse JSON output: {e}")

    return None


def run_container(task_dir: str, battle_id: str = None) -> str:
    cybench_dir = Path(__file__).resolve().parents[2] / "resources" / "cybench"
    print(f"cybench_dir: {cybench_dir}/setup_cybench_env.py")
    volumes = {
        str(cybench_dir / "agent"): {"bind": "/app/agent", "mode": "ro"},
        str(cybench_dir / "setup_cybench_env.py"): {
            "bind": "/app/setup_cybench_env.py",
            "mode": "ro",
        },
        str(cybench_dir / "run_task.py"): {
            "bind": "/app/run_task.py",
            "mode": "ro",
        },
    }
    env_vars = {}
    env_file = cybench_dir / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    if "DOCKER_NETWORK_DRIVER" not in env_vars:
        env_vars["DOCKER_NETWORK_DRIVER"] = "bridge"
    print("Running Docker container for task_dir:", task_dir)
    container_name = _get_container_name(battle_id)
    # Use a long-running command to keep the container alive
    command = ["tail", "-f", "/dev/null"]
    try:
        print("Pulling latest image...")
        client.images.pull(image_name)
        container = client.containers.run(
            image=image_name,
            command=command,
            name=container_name,
            network=network_name,
            volumes=volumes,
            environment=env_vars,
            privileged=True,
            detach=True,
            remove=False,
            stdout=True,
            stderr=True,
            cgroupns="host",
        )
        containers[container_name] = container
        return ""  # No logs yet, since nothing has run
    except Exception as e:
        try:
            container = client.containers.get(container_name)
            container.remove(force=True)
            if container_name in containers:
                del containers[container_name]
        except:
            pass
        raise e


@tool
def setup_cybench_task(task_dir: str, battle_id: str = None) -> Dict[Any, Any]:
    print(f"\033[32mSetting up cybench task: {task_dir}\033[0m")
    cleanup_existing_container(battle_id)
    create_network_if_needed()
    run_container(task_dir, battle_id)
    container_name = _get_container_name(battle_id)
    container = client.containers.get(container_name)
    # Run the setup script inside the container
    exec_result = container.exec_run(
        f"python3 /app/setup_cybench_env.py --task_dir {task_dir}",
        stdout=True,
        stderr=True,
    )
    output = exec_result.output.decode("utf-8")
    json_result = parse_json_output(output)
    if json_result is None:
        print("Warning: Could not parse JSON output, trying text extraction")
        return {"output": output, "prompt": None}
    print(f"\033[32mCybench task setup complete\033[0m")
    return json_result


@tool
def execute_command_in_container(command: str, battle_id: str = None) -> str:
    """
    This tool is used to execute a command in the running container and return the output.
    command: The command to execute in the container.
    battle_id: The battle_id for the container to execute the command in.

    Example:
    ```
    command: ls -la /tmp/cyber-bench
    battle_id: example123
    ```

    Returns:
        str: The output of the command.
    """
    logger.info(f"\033[34mExecuting command in container: {command}\033[0m")
    container_name = _get_container_name(battle_id)
    try:
        container = client.containers.get(container_name)

        # Check if container is running
        if container.status != "running":
            logger.warning(
                f"Container {container_name} is not running, restarting it..."
            )
            container.start()

        # Execute command in the running container
        exec_result = container.exec_run(command, stdout=True, stderr=True)
        output = exec_result.output.decode("utf-8")
        logger.info(f"Output: {output}")
        return output

    except docker.errors.NotFound:
        print(f"Container {container_name} not found, please run a task first")
        return ""
    except Exception as e:
        print(f"Error executing command in container: {e}")
        return ""


@tool
def destroy_container(
    battle_id: str = None, remove_network: bool = False
) -> bool:
    """
    Destroy the container and optionally remove the network.

    Args:
        battle_id: The battle_id for the container to destroy (None for default)
        remove_network: If True, also remove the shared network if no other containers are using it

    Returns:
        bool: True if container was successfully destroyed, False otherwise
    """
    container_name = _get_container_name(battle_id)
    try:
        # Get the container
        container = client.containers.get(container_name)

        # Stop the container if it's running
        if container.status == "running":
            print(f"Stopping container: {container_name}")
            container.stop(timeout=10)

        # Remove the container
        print(f"Removing container: {container_name}")
        container.remove(force=True)
        print(f"Successfully destroyed container: {container_name}")

        # Optionally remove the network
        if remove_network:
            _cleanup_network()

        if container_name in containers:
            del containers[container_name]

        return True

    except docker.errors.NotFound:
        print(
            f"Container {container_name} not found - already destroyed or never created"
        )
        return True
    except Exception as e:
        print(f"Error destroying container {container_name}: {e}")
        return False


@tool
def update_battle_process(stage: int, process: str) -> bool:
    """
    Update the battle process.
    Stage: The stage of the game.
    Process: The process of the game.
    """
    logger.info(
        f"\033[95mUpdating battle process for stage {stage}: {process}\033[0m"
    )
    return True


def _cleanup_network():
    """
    Remove the shared network if no other containers are using it.
    This is a helper method for destroy_container.
    """
    try:
        network = client.networks.get(network_name)

        # Check if any containers are still connected to this network
        connected_containers = network.attrs.get("Containers", {})

        if not connected_containers:
            print(f"Removing unused network: {network_name}")
            network.remove()
            print(f"Successfully removed network: {network_name}")
        else:
            print(
                f"Network {network_name} still has connected containers, keeping it"
            )

    except docker.errors.NotFound:
        print(
            f"Network {network_name} not found - already removed or never created"
        )
    except Exception as e:
        print(f"Warning: Failed to remove network {network_name}: {e}")


def _get_container_name(battle_id: str = None) -> str:
    return f"cybench_{battle_id}" if battle_id else "cybench"


def main():
    """Main function to handle command line execution"""
    # Example: pass battle_id and task_dir as arguments
    battle_id = "example123"  # Replace with dynamic value as needed
    task_dir = "benchmark/hackthebox/cyber-apocalypse-2024/crypto/[Very Easy] Dynastic"
    try:
        results = setup_cybench_task(task_dir, battle_id=battle_id)
        print("Testing command execution in container...")
        ls_output = execute_command_in_container(
            "ls -la /tmp/cyber-bench", battle_id=battle_id
        )
        print(ls_output)
        if "prompt" in results:
            print("\n" + "=" * 50)
            print("EXTRACTED PROMPT:")
            print("=" * 50)
            print(results["prompt"])
            print("=" * 50)
            print(results["task"]["subtasks"])
            return results["prompt"]
        else:
            print("Warning: No prompt found in results")
            return None
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
