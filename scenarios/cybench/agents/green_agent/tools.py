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
import asyncio
from uuid import uuid4
import time
import docker
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import httpx
from collections import defaultdict
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    Message,
    MessageSendParams,
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    Role,
    Part,
    TextPart,
    AgentCard,
)


from agentbeats import tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cybench_dir = Path(__file__).resolve().parents[2] / "resources" / "cybench"


########################################################
# Agent communication tools
########################################################

httpx_client: httpx.AsyncClient = httpx.AsyncClient()

battle_start_times = defaultdict(float)
battle_cumulative_times = defaultdict(float)


async def _make_client(base_url: str) -> A2AClient:
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url,
    )
    card: AgentCard | None = await resolver.get_agent_card(
        relative_card_path="/.well-known/agent.json"
    )
    if card is None:
        raise RuntimeError(f"Failed to resolve agent card from {base_url}")
    return A2AClient(httpx_client=httpx_client, agent_card=card)


@tool
def get_task_dir(task_index: int) -> str:
    """
    Get the task directory (task_dir) for the given task index.
    """
    # read the list from "task_list.txt" with readlines()
    try:
        with open("agents/green_agent/task_list.txt", "r") as f:
            task_list = f.readlines()
    except FileNotFoundError:
        logger.error("Task list file not found")
        logger.error(f"Current directory: {Path.cwd()}")
        return None
    # return the task description for the given task index
    logger.info(f"Task index: {task_index}")
    logger.info(f"Task list: {task_list}")
    return task_list[task_index]


@tool
async def talk_to_red_agent(
    query: str, target_url: str, battle_id: str, timeout_seconds: float = 120.0
) -> str:
    """Talk to a red or blue agent at the given URL with a query. Tracks cumulative time for the battle."""
    logging.info(
        f"Talking to agent at {target_url} with query: {query} for battle {battle_id}"
    )
    logging.info(f"Timeout: {timeout_seconds}")

    # Check if battle has started, if not start the stopwatch
    if (
        battle_id not in battle_start_times
        or battle_start_times[battle_id] == 0
    ):
        battle_start_times[battle_id] = time.time()
        logging.info(f"Starting stopwatch for battle {battle_id}")
    else:
        logging.info(
            f"Continuing existing battle {battle_id} (started at {battle_start_times[battle_id]})"
        )

    client = await _make_client(target_url)
    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=query))],
            messageId=uuid4().hex,
            taskId=None,  # Let the red agent create a new task
        )
    )
    req = SendStreamingMessageRequest(id=str(uuid4()), params=params)
    chunks: List[str] = []
    message_start_time = time.time()
    try:

        async def stream_reply():
            async for chunk in client.send_message_streaming(req):
                # Log the chunk for debugging
                logging.debug(f"Received chunk: {chunk}")

                if not isinstance(
                    chunk.root, SendStreamingMessageSuccessResponse
                ):
                    continue
                event = chunk.root.result

                # Handle TaskArtifactUpdateEvent (final response)
                if isinstance(event, TaskArtifactUpdateEvent):
                    for p in event.artifact.parts:
                        if isinstance(p.root, TextPart):
                            chunks.append(p.root.text)
                # Handle TaskStatusUpdateEvent (status messages)
                elif isinstance(event, TaskStatusUpdateEvent):
                    msg = event.status.message
                    if msg:
                        for p in msg.parts:
                            if isinstance(p.root, TextPart):
                                chunks.append(p.root.text)
                # Handle any other event type that might contain text
                else:
                    # Try to extract text from any other event type
                    if hasattr(event, "message") and event.message:
                        for p in event.message.parts:
                            if isinstance(p.root, TextPart):
                                chunks.append(p.root.text)
                    elif hasattr(event, "text"):
                        chunks.append(str(event.text))
                    elif hasattr(event, "content"):
                        chunks.append(str(event.content))

        await asyncio.wait_for(stream_reply(), timeout=timeout_seconds)
        message_end_time = time.time()
        message_elapsed = message_end_time - message_start_time

        # Update cumulative time for this battle
        battle_cumulative_times[battle_id] += message_elapsed

        ans = "".join(chunks).strip() or "No response from agent."
        logging.info(ans)
        logging.info(f"Message response time: {message_elapsed:.2f} seconds")
        logging.info(
            f"Battle {battle_id} cumulative time: {battle_cumulative_times[battle_id]:.2f} seconds"
        )

        return f"{ans}\n[Message response time: {message_elapsed:.2f} seconds]\n[Battle cumulative time: {battle_cumulative_times[battle_id]:.2f} seconds]"
    except asyncio.TimeoutError:
        # Still count timeout towards cumulative time
        message_end_time = time.time()
        message_elapsed = message_end_time - message_start_time
        battle_cumulative_times[battle_id] += message_elapsed

        logging.warning(
            f"[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds."
        )
        logging.info(
            f"Battle {battle_id} cumulative time: {battle_cumulative_times[battle_id]:.2f} seconds"
        )
        return f"[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds.\n[Battle cumulative time: {battle_cumulative_times[battle_id]:.2f} seconds]"


@tool
async def get_attack_cumulative_time(battle_id: str) -> str:
    """Get the cumulative time the red agent has spent attacking the target."""
    if battle_id not in battle_cumulative_times:
        return f"No communication time recorded for battle {battle_id}"

    cumulative_time = battle_cumulative_times[battle_id]
    start_time = battle_start_times.get(battle_id, 0)

    if start_time == 0:
        return f"Battle {battle_id} has no recorded start time"

    current_time = time.time()
    total_battle_time = current_time - start_time

    return (
        f"Battle {battle_id} stats:\n"
        # f"- Cumulative red agent attack time: {cumulative_time:.2f} seconds\n"
        f"- Red agent attack time: {total_battle_time:.2f} seconds\n"
    )


@tool
async def reset_battle_timing(battle_id: str) -> str:
    """Reset the timing data for a specific battle."""
    if battle_id in battle_start_times:
        del battle_start_times[battle_id]
    if battle_id in battle_cumulative_times:
        del battle_cumulative_times[battle_id]

    return f"Timing data reset for battle {battle_id}"


########################################################
# Cybench tools
########################################################


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
    """Run the Docker container for the given task_dir and battle_id"""
    logger.info(f"cybench_dir: {cybench_dir}/setup_cybench_env.py")
    volumes = {
        str(cybench_dir / "agent"): {"bind": "/app/agent", "mode": "ro"},
        str(cybench_dir / "setup_cybench_env.py"): {
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
    logger.info(f"Running Docker container for task_dir: {task_dir}")
    container_name = _get_container_name(battle_id)
    # Build the command to run inside the container
    command = [
        "--task_dir",
        task_dir,
    ]
    try:
        logger.info("Pulling latest image...")
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

        # Wait for the setup process to complete and get the IMPORTANT logs
        result = container.wait()
        logs = container.logs(stdout=True, stderr=True).decode("utf-8")
        with open("/tmp/benchmark-latest.log", "w") as f:
            f.write(logs)

        if result["StatusCode"] != 0:
            logger.error(
                f"Container setup failed with status code {result['StatusCode']}"
            )
            logger.error(f"Logs: {logs}")
            raise RuntimeError(
                f"Container setup failed with status code {result['StatusCode']}"
            )

        # Now restart the container with a command that keeps it alive
        logger.info(
            "Setup completed successfully. Restarting container to keep it alive..."
        )
        container.restart()

        # Execute a command to keep the container running indefinitely
        import time

        time.sleep(2)  # Give restart a moment
        container.exec_run(["sh", "-c", "tail -f /dev/null"], detach=True)

        logger.info(
            f"Container {container_name} setup complete and staying alive for commands"
        )
        return logs
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
    """
    This is the first tool to be called by the green agent.
    It will setup the cybench task by
    1. Setting up the docker environment
    2. Preparing the task environment
    3. Returning the results

    Returns:
        Dict[Any, Any]: The results of the task.
        {
            "challenge_prompt": str, # The challenge prompt to be used by the agent to solve the task
            "task": {
                "name": str,
                "path": str,
                "easy_prompt": str,
                "subtasks": List[Dict[Any, Any]],
            },
            "task_objective": str,
        }

        Subtasks:
        {
            "question": str,
            "answer": str,
            "hint": str,
            "annotator_note": str,
            "answer_format": str,
            "commands": List[str],
        }
    """
    # self.validate_current_directory()
    logger.info(f"Setting up cybench task: {task_dir}")
    cleanup_existing_container(battle_id)
    create_network_if_needed()
    start_script = os.path.join(cybench_dir, task_dir, "start_docker.sh")
    execute_task_script(start_script, "start_docker.sh")
    try:
        output = run_container(task_dir, battle_id)
        json_result = parse_json_output(output)
        if json_result is None:
            logger.warning(
                "Warning: Could not parse JSON output, trying text extraction"
            )
            return {"output": output, "prompt": None}
        logger.info("Cybench task setup complete")
        return json_result
    finally:
        # stop_script = os.path.join(task_dir, "stop_docker.sh")
        # self.execute_task_script(stop_script, "stop_docker.sh")
        pass


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
