# -*- coding: utf-8 -*-

"""
This MCP is used to setup the Docker environment for the Sec-Bench CVE instance.

Todo:
- [ ] Support for tracking a docker container env for each CVE instance / battle ID
- [ ] How to hide some orchestration tools from BLUE & RED agents?

For demo, the docker path will be:
hwiwonlee/secb.eval.x86_64.gpac.cve-2023-5586:poc
"""

import logging
from fastmcp import FastMCP
import docker
import os
from pathlib import Path
from datetime import datetime
import json
from datasets import load_dataset

# Docker connection settings
DOCKER_SOCKET_PATHS = [
    str(
        Path.home() / ".docker/run/docker.sock"
    ),  # macOS Docker Desktop path (confirmed working)
    "/var/run/docker.sock",  # Standard Linux path
    str(Path.home() / ".docker/desktop/docker.sock"),  # Alternative macOS path
]


# Configure logging once
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
logger = logging.getLogger(__name__)

# Remove console handler to avoid duplicates
logger.handlers = []
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("[%(levelname)s] [%(asctime)s] %(message)s")
)
logger.addHandler(handler)


server = FastMCP(
    "Open MCP for AgentBeats Battle Arena",
    host="0.0.0.0",
    port=9001,
)

DOCKER_BATTLE_CONTAINERS: dict[str, dict[str, str]] = {}

BACKEND_URL = "http://localhost:9000"

# Add this constant at the top level with other constants
BATTLE_LOG_PATH = Path("scenarios/sec_bench/battle_log.json")


@server.tool()
def echo(message: str) -> str:
    """
    Echo the input message.
    """
    logger.info("Echoing message: %s", message)
    return f"Echo: {message}"


########################################################
# Docker tools
########################################################


def get_docker_client():
    """Get a Docker client using available connection methods."""
    # Try Unix socket connections first
    for socket_path in DOCKER_SOCKET_PATHS:
        if os.path.exists(socket_path):
            try:
                return docker.DockerClient(base_url=f"unix://{socket_path}")
            except Exception:
                continue

    # Fallback to TCP
    try:
        return docker.from_env()
    except Exception as e:
        raise Exception(
            f"Could not connect to Docker daemon. Is Docker running? Error: {e}"
        )


@server.tool()
def setup_docker_env(
    battle_id: str,
    docker_image_name: str,
) -> str:
    """
    Setup the Docker environment for the Sec-Bench CVE instance.
    This is only for the Green agent.
    """
    logger.info(f"Setting up docker env for battle {battle_id}...")

    try:
        client = get_docker_client()
        container_name = f"secb_battle_{battle_id}"

        try:
            existing_container = client.containers.get(container_name)
            message = f"Container {container_name} already exists for battle {battle_id} (status: {existing_container.status})."
            logger.info(message)
            return message
        except docker.errors.NotFound:
            pass

        logger.info(f"Pulling image {docker_image_name}...")
        client.images.pull(docker_image_name)
        container = client.containers.run(
            docker_image_name,
            "sleep infinity",
            name=container_name,
            detach=True,
        )
        DOCKER_BATTLE_CONTAINERS[battle_id] = {
            "container_name": container_name
        }
        message = f"Container {container_name} started for battle {battle_id}."
        logger.info(message)
        return message
    except Exception as e:
        error_msg = f"Error setting up docker env: {e}"
        logger.error(error_msg)
        return error_msg


@server.tool()
def destroy_docker_env(
    battle_id: str,
) -> str:
    """
    Destroy and remove the Docker container for the given battle_id.
    """
    try:
        client = get_docker_client()
        container_name = f"secb_battle_{battle_id}"
        try:
            container = client.containers.get(container_name)
            container.remove(force=True)
            message = f"Container {container_name} for battle {battle_id} has been destroyed and removed."
            logger.info(message)
            return message
        except docker.errors.NotFound:
            message = f"No container found for battle_id {battle_id}."
            logger.warning(message)
            return message
    except Exception as e:
        error_msg = f"Error destroying docker env: {e}"
        logger.error(error_msg)
        return error_msg


@server.tool()
def run_terminal_command_in_docker(
    battle_id: str,
    command: str,
) -> str:
    """
    Run a terminal command in the specified docker container for the given battle_id.
    This is for any Red, Blue, or Green agent.
    """
    try:
        client = get_docker_client()
        container_name = f"secb_battle_{battle_id}"
        try:
            container = client.containers.get(container_name)
            exec_log = container.exec_run(command)
            message = exec_log.output.decode()
            logger.info(f"Command output for {container_name}: {message}")
            return message
        except docker.errors.NotFound:
            message = f"No container found for battle_id {battle_id}."
            logger.warning(message)
            return message
    except Exception as e:
        error_msg = f"Error running command: {e}"
        logger.error(error_msg)
        return error_msg


########################################################
# Battle progress tracking
########################################################


@server.tool()
def update_battle_process(
    battle_id: str,
    message: str,
    reported_by: str,
    detail: dict = None,
) -> str:
    """
    Log intermediate steps and information during the battle.

    Parameters:
    - battle_id: The unique battle session identifier
    - message: Simple, human-readable description of what happened
    - reported_by: The agent/role reporting this information ("green_agent", "red_agent", or "blue_agent")
    - detail: Optional structured data with specific event details
    """
    try:
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "battle_id": battle_id,
            "message": message,
            "reported_by": reported_by,
            "detail": detail or {},
        }

        # Log to console
        logger.info(
            f"Battle progress update for {battle_id}: {message} (by {reported_by})"
        )
        if detail:
            logger.debug(f"Details: {detail}")

        # Save to JSON file
        log_file = BATTLE_LOG_PATH
        # Create directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = {"battle_logs": []}

        logs["battle_logs"].append(log_entry)

        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)

        # log where it was saved to
        logger.info(f"Battle progress recorded to {log_file}")

        return f"Battle progress recorded: {message}"
    except Exception as e:
        error_msg = f"Error updating battle progress: {e}"
        logger.error(error_msg)
        return error_msg


@server.tool()
def report_on_battle_end(
    battle_id: str,
    winner: str,
    score: dict,
    detail: dict = None,
) -> str:
    """
    Report the final battle result.

    Parameters:
    - battle_id: The unique battle session identifier
    - winner: Either "red_agent" or "blue_agent"
    - score: Dictionary containing scoring details
    - detail: Optional additional information about the battle outcome
    """
    try:
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "battle_id": battle_id,
            "type": "battle_end",
            "winner": winner,
            "score": score,
            "detail": detail or {},
        }

        # Log to console
        logger.info(f"Battle {battle_id} ended. Winner: {winner}")
        logger.info(f"Score: {score}")
        if detail:
            logger.debug(f"Details: {detail}")

        # Save to JSON file
        log_file = BATTLE_LOG_PATH
        # Create directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = {"battle_logs": []}

        logs["battle_logs"].append(log_entry)

        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)

        return f"Battle end recorded. Winner: {winner}"
    except Exception as e:
        error_msg = f"Error reporting battle end: {e}"
        logger.error(error_msg)
        return error_msg


########################################################
# Sec-Bench Huggingface Dataset tools
########################################################


@server.tool()
def get_workspace_dir_name(instance_id: str) -> str:
    """
    Get the workspace directory name for a given instance ID from the SEC-bench dataset.

    Parameters:
    - instance_id: The unique identifier for the instance in the dataset
    """
    try:
        # Load the SEC-bench dataset
        dataset = load_dataset("hwiwonlee/secb", split="test")

        # Find the instance with matching ID
        for instance in dataset:
            if instance["id"] == instance_id:
                return instance["workspace_dir_name"]

        return f"Error: No instance found with ID {instance_id}"
    except Exception as e:
        error_msg = f"Error getting workspace directory name: {e}"
        logger.error(error_msg)
        return error_msg


@server.tool()
def get_sanitizer_report(instance_id: str) -> str:
    """
    Get the sanitizer report for a given instance ID from the SEC-bench dataset.

    Parameters:
    - instance_id: The unique identifier for the instance in the dataset
    """
    try:
        # Load the SEC-bench dataset
        dataset = load_dataset("hwiwonlee/secb", split="test")

        # Find the instance with matching ID
        for instance in dataset:
            if instance["id"] == instance_id:
                return instance["sanitizer_report"]

        return f"Error: No instance found with ID {instance_id}"
    except Exception as e:
        error_msg = f"Error getting sanitizer report: {e}"
        logger.error(error_msg)
        return error_msg


@server.tool()
def get_bug_report(instance_id: str) -> str:
    """
    Get the bug report for a given instance ID from the SEC-bench dataset.

    Parameters:
    - instance_id: The unique identifier for the instance in the dataset
    """
    try:
        # Load the SEC-bench dataset
        dataset = load_dataset("hwiwonlee/secb", split="test")

        # Find the instance with matching ID
        for instance in dataset:
            if instance["id"] == instance_id:
                return instance["bug_report"]

        return f"Error: No instance found with ID {instance_id}"
    except Exception as e:
        error_msg = f"Error getting bug report: {e}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    server.run(
        transport="sse",
        log_level="ERROR",
    )
