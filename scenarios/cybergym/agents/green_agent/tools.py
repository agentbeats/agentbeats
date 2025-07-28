# -*- coding:utf-8 -*-

import asyncio
import subprocess
import docker
import os
import time
from typing import List
from uuid import uuid4
from pathlib import Path
import httpx
from agentbeats import tool
import logging
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

# Path constants
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CYBERGYM_PATH = (
    PROJECT_ROOT / "scenarios" / "cybergym" / "resources" / "cybergym"
)
POC_SAVE_DIR = CYBERGYM_PATH / "poc_save_dir"
CYBERGYM_SERVER_DATA_DIR = CYBERGYM_PATH / "oss-fuzz-data"
CYBERGYM_DATA_DIR = CYBERGYM_PATH / "cybergym_data" / "data"
CYBERGYM_TASK_DIR = CYBERGYM_PATH / "task_folder"

# Docker connection settings
DOCKER_SOCKET_PATHS = [
    str(
        Path.home() / ".docker/run/docker.sock"
    ),  # macOS Docker Desktop path (confirmed working)
    "/var/run/docker.sock",  # Standard Linux path
    str(Path.home() / ".docker/desktop/docker.sock"),  # Alternative macOS path
]

httpx_client: httpx.AsyncClient = httpx.AsyncClient()


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

battle_start_times = defaultdict(float)
battle_cumulative_times = defaultdict(float)


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
async def talk_to_red_or_blue_agent(
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


@tool
async def start_cybergym_server(port: int = 8666) -> str:
    """Start the Cybergym server on the specified port."""
    logging.info(f"Starting Cybergym server on port {port}")
    logging.info(f"POC_SAVE_DIR: {POC_SAVE_DIR}")
    logging.info(f"CYBERGYM_SERVER_DATA_DIR: {CYBERGYM_SERVER_DATA_DIR}")
    cmd = [
        f"cd {PROJECT_ROOT} &&",
        "ls venv &&",
        "source venv/bin/activate &&",
        "python -m cybergym.server",
        f"--host 0.0.0.0",
        f"--port {port}",
        f"--log_dir {POC_SAVE_DIR}",
        f"--db_path {POC_SAVE_DIR}/poc.db",
        f"--cybergym_oss_fuzz_path {CYBERGYM_SERVER_DATA_DIR}",
    ]
    cmd_str = " ".join(cmd)
    logging.info(f"Running command: {cmd_str}")
    try:
        process = subprocess.Popen(cmd_str, shell=True)
        logging.info(f"Cybergym server started with PID: {process.pid}")
        logging.info(f"--------------------------------")
        return (
            f"Cybergym server started on port {port} with PID: {process.pid}"
        )
    except Exception as e:
        logging.error(f"Failed to start Cybergym server: {e}")
        return f"Failed to start Cybergym server: {e}"


@tool
async def generate_cybergym_task(task_id: str, battle_id: str) -> str:
    """Generate a Cybergym task with the specified task ID."""
    cmd = [
        f"cd {PROJECT_ROOT} &&",
        "ls venv &&",
        "source venv/bin/activate &&",
        "python -m cybergym.task.gen_task",
        f"--task-id {task_id}",
        f"--out-dir {str(CYBERGYM_TASK_DIR)}_{battle_id}",
        f"--data-dir {CYBERGYM_DATA_DIR}",
        f"--server http://host.docker.internal:8666",
        f"--difficulty level1",
    ]
    cmd_str = " ".join(cmd)
    logging.info(f"Running command: {cmd_str}")
    try:
        result = subprocess.run(
            cmd_str, capture_output=True, text=True, shell=True
        )
        logging.info(f"stdout: {result.stdout.strip()}")
        logging.info(f"stderr: {result.stderr.strip()}")
        logging.info(f"Return code: {result.returncode}")
        return f"stdout: {result.stdout}\nstderr: {result.stderr}"
    except Exception as e:
        logging.error(f"Failed to generate cybergym task: {e}")
        return f"Failed to generate cybergym task: {e}"


@tool
async def setup_docker_env(
    battle_id: str, docker_image_name: str = "cybergym/oss-fuzz-base-runner"
) -> str:
    """
    Setup the Docker environment for the Sec-Bench CVE instance.
    This is only for the Green agent.
    """
    logging.info(f"Setting up docker env for battle {battle_id}...")

    try:
        client = get_docker_client()
        container_name = f"cybergym_{battle_id}"

        try:
            existing_container = client.containers.get(container_name)
            message = f"Container {container_name} already exists for battle {battle_id} (status: {existing_container.status})."
            logging.info(message)
            return message
        except docker.errors.NotFound:
            pass

        logging.info(f"Pulling image {docker_image_name}...")
        client.images.pull(docker_image_name)
        container = client.containers.run(
            docker_image_name,
            "sleep infinity",
            name=container_name,
            detach=True,
            extra_hosts={"host.docker.internal": "host-gateway"},
            volumes={
                f"{str(CYBERGYM_TASK_DIR)}_{battle_id}": {
                    "bind": "/cybergym_task_dir",
                    "mode": "rw",
                }
            },
        )
        message = f"Container {container_name} started for battle {battle_id}."
        logging.info(message)
        return message
    except Exception as e:
        error_msg = f"Error setting up docker env: {e}"
        logging.error(error_msg)
        return error_msg


@tool
async def destroy_docker_env(battle_id: str) -> str:
    """
    Destroy and remove the Docker container for the given battle_id.
    """
    try:
        client = get_docker_client()
        container_name = f"cybergym_{battle_id}"
        try:
            container = client.containers.get(container_name)
            container.remove(force=True)
            message = f"Container {container_name} for battle {battle_id} has been destroyed and removed."
            logging.info(message)
            return message
        except docker.errors.NotFound:
            message = f"No container found for battle_id {battle_id}."
            logging.warning(message)
            return message
    except Exception as e:
        error_msg = f"Error destroying docker env: {e}"
        logging.error(error_msg)
        return error_msg
