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
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)
CYBERGYM_PATH = os.path.join(PROJECT_ROOT, "external", "cybergym")
POC_SAVE_DIR = os.path.join(CYBERGYM_PATH, "poc_save_dir")
CYBERGYM_SERVER_DATA_DIR = os.path.join(CYBERGYM_PATH, "cybergym_data", "data")
CYBERGYM_TASK_DIR = os.path.join(CYBERGYM_PATH, "task_folder")

# Docker connection settings
DOCKER_SOCKET_PATHS = [
    str(
        Path.home() / ".docker/run/docker.sock"
    ),  # macOS Docker Desktop path (confirmed working)
    "/var/run/docker.sock",  # Standard Linux path
    str(Path.home() / ".docker/desktop/docker.sock"),  # Alternative macOS path
]

DOCKER_IMAGES = ["cybergym/oss-fuzz-base-runner", "n132/arvo"]

httpx_client: httpx.AsyncClient = httpx.AsyncClient()


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
    query: str, target_url: str, timeout_seconds: float = 120.0
) -> str:
    """Talk to a red or blue agent at the given URL with a query."""
    logging.info(f"Talking to agent at {target_url} with query: {query}")
    logging.info(f"Timeout: {timeout_seconds}")
    client = await _make_client(target_url)
    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=query))],
            messageId=uuid4().hex,
            taskId=uuid4().hex,
        )
    )
    req = SendStreamingMessageRequest(id=str(uuid4()), params=params)
    chunks: List[str] = []
    start_time = time.time()
    try:

        async def stream_reply():
            async for chunk in client.send_message_streaming(req):
                if not isinstance(
                    chunk.root, SendStreamingMessageSuccessResponse
                ):
                    continue
                event = chunk.root.result
                if isinstance(event, TaskArtifactUpdateEvent):
                    for p in event.artifact.parts:
                        if isinstance(p.root, TextPart):
                            chunks.append(p.root.text)
                elif isinstance(event, TaskStatusUpdateEvent):
                    msg = event.status.message
                    if msg:
                        for p in msg.parts:
                            if isinstance(p.root, TextPart):
                                chunks.append(p.root.text)

        await asyncio.wait_for(stream_reply(), timeout=timeout_seconds)
        end_time = time.time()
        elapsed = end_time - start_time
        ans = "".join(chunks).strip() or "No response from agent."
        logging.info(ans)
        return f"{ans}\n[Response time: {elapsed:.2f} seconds]"
    except asyncio.TimeoutError:
        logging.warning(
            f"[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds."
        )
        return f"[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds."


@tool
async def start_cybergym_server(port: int = 8666) -> str:
    """Start the Cybergym server on the specified port."""
    logging.info(f"Starting Cybergym server on port {port}")
    logging.info(f"POC_SAVE_DIR: {POC_SAVE_DIR}")
    logging.info(f"CYBERGYM_SERVER_DATA_DIR: {CYBERGYM_SERVER_DATA_DIR}")
    cmd = [
        f"cd {PROJECT_ROOT} &&",
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
async def generate_cybergym_task(task_id: str = "arvo:368") -> str:
    """Generate a Cybergym task with the specified task ID."""
    OUT_DIR = CYBERGYM_TASK_DIR
    CYBERGYM_DATA_DIR = CYBERGYM_SERVER_DATA_DIR
    cmd = [
        f"cd {PROJECT_ROOT} &&",
        "source venv/bin/activate &&",
        "python -m cybergym.task.gen_task",
        f"--task-id {task_id}",
        f"--out-dir {OUT_DIR}",
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
async def setup_docker_env(battle_id: str, docker_image_name: str) -> str:
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
                str(CYBERGYM_TASK_DIR): {
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
