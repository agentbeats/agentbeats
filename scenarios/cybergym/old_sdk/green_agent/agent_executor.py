# -*- coding:utf-8 -*-

import httpx
from typing import Dict, List
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerSse
from uuid import uuid4
import os
import subprocess
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart
from a2a.utils import new_task, new_agent_text_message
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
import os
import asyncio
from openai import AsyncOpenAI
from agents import ModelProvider, OpenAIChatCompletionsModel, RunConfig
from agents import set_tracing_disabled
import docker
from pathlib import Path

set_tracing_disabled(disabled=True)
from agents import Model
import logging
import time

from prompt import GREEN_AGENT_PROMPT

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


logging.basicConfig(level=logging.INFO)

OPENROUTER_BASE_URL = os.getenv(
    "OPENAI_API_BASE", "https://openrouter.ai/api/v1"
)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "o4-mini"

custom_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY
)


class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name or MODEL_NAME, openai_client=custom_client
        )


CUSTOM_MODEL_PROVIDER = CustomModelProvider()


class GreenAgent:
    def __init__(self, mcp_url: str, docker_mcp_url: str = None) -> None:
        """Initialize the Green Agent with its prompt and tools.
        Args:
            mcp_url: URL for the MCP server
            docker_mcp_url: URL for the Docker MCP server (optional)
        """
        print("[GreenAgent] ENV OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
        print(
            "[GreenAgent] ENV OPENAI_API_BASE:", os.getenv("OPENAI_API_BASE")
        )
        print("[GreenAgent] Model for main_agent:", "o4-mini")
        self._httpx_client: httpx.AsyncClient = httpx.AsyncClient()

        # URL for the MCP server
        self.mcp_url = mcp_url
        self.mcp_servers = []
        self.mcp_servers.append(
            MCPServerSse(
                name="Open MCP for AgentBeats Battle Arena",
                client_session_timeout_seconds=600,
                params={
                    "url": self.mcp_url,
                    "timeout": 600,
                },
                cache_tools_list=True,
            )
        )
        if docker_mcp_url:
            self.mcp_servers.append(
                MCPServerSse(
                    name="Docker Handler MCP for Sec-Bench Battle Arena (Docker + Sec-Bench CVE Instance Handler)",
                    client_session_timeout_seconds=600,
                    params={
                        "url": docker_mcp_url,
                        "timeout": 600,
                    },
                    cache_tools_list=True,
                )
            )
        print("MCP servers connected:", self.mcp_servers)
        print("Docker MCP server connected:", docker_mcp_url)
        self.mcp_servers_connected = False

        # Initialize chat history and tools
        self.chat_history: List[Dict[str, str]] = []
        self.tool_list = [
            self._create_talk_to_agent_tool(),
            self._create_start_cybergym_server_tool(),
            self._create_generate_cybergym_task_tool(),
            self._create_setup_docker_env_tool(),
            self._create_destroy_docker_env_tool(),
        ]

    async def ensure_mcp_connected(self) -> None:
        """Ensure the MCP server is connected."""
        if not self.mcp_servers_connected:
            for server in self.mcp_servers:
                await server.connect()

            self.main_agent = Agent(
                name="Green Agent",
                instructions=GREEN_AGENT_PROMPT,
                model="o4-mini",
                tools=self.tool_list,
                mcp_servers=self.mcp_servers,
            )

            self.mcp_servers_connected = True

    async def _make_client(self, base_url: str) -> A2AClient:
        resolver = A2ACardResolver(
            httpx_client=self._httpx_client,
            base_url=base_url,
        )
        card: AgentCard | None = await resolver.get_agent_card(
            relative_card_path="/.well-known/agent.json"
        )
        if card is None:
            raise RuntimeError(f"Failed to resolve agent card from {base_url}")
        return A2AClient(httpx_client=self._httpx_client, agent_card=card)

    def _create_talk_to_agent_tool(self):
        @function_tool(name_override="talk_to_red_or_blue_agent")
        async def _talk_to_agent(
            query: str, target_url: str, timeout_seconds: float = 120.0
        ) -> str:
            logging.info(
                f"Talking to agent at {target_url} with query: {query}"
            )
            logging.info(f"Timeout: {timeout_seconds}")
            client = await self._make_client(target_url)
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
                return "[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds."

        return _talk_to_agent

    def _create_start_cybergym_server_tool(self):
        @function_tool(name_override="start_cybergym_server")
        async def _start_cybergym_server(
            port: int = 8666,
        ) -> str:
            logging.info(f"Starting Cybergym server on port {port}")
            logging.info(f"POC_SAVE_DIR: {POC_SAVE_DIR}")
            logging.info(
                f"CYBERGYM_SERVER_DATA_DIR: {CYBERGYM_SERVER_DATA_DIR}"
            )
            cmd = [
                "source venv/bin/activate",
                "&&",
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
                logging.info(
                    f"Cybergym server started with PID: {process.pid}"
                )
                logging.info(f"--------------------------------")
                return f"Cybergym server started on port {port} with PID: {process.pid}"
            except Exception as e:
                logging.error(f"Failed to start Cybergym server: {e}")
                return f"Failed to start Cybergym server: {e}"

        return _start_cybergym_server

    def _create_generate_cybergym_task_tool(self):
        @function_tool(name_override="generate_cybergym_task")
        async def _generate_cybergym_task(task_id: str = "arvo:368") -> str:
            OUT_DIR = CYBERGYM_TASK_DIR
            CYBERGYM_DATA_DIR = CYBERGYM_SERVER_DATA_DIR
            cmd = [
                "source venv/bin/activate",
                "&&",
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

        return _generate_cybergym_task

    def _create_setup_docker_env_tool(self):
        @function_tool(name_override="setup_docker_env")
        async def _setup_docker_env(
            battle_id: str,
            docker_image_name: str,
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

        return _setup_docker_env

    def _create_destroy_docker_env_tool(self):
        @function_tool(name_override="destroy_docker_env")
        async def _destroy_docker_env(
            battle_id: str,
        ) -> str:
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

        return _destroy_docker_env

    async def invoke(self, context) -> str:
        print(
            context.get_user_input(),
            "=========================================GREEN INPUT",
        )
        await self.ensure_mcp_connected()
        query_ctx = self.chat_history + [
            {"content": context.get_user_input(), "role": "user"}
        ]
        result = await Runner.run(
            self.main_agent,
            query_ctx,
            max_turns=50,
            run_config=RunConfig(model_provider=CUSTOM_MODEL_PROVIDER),
        )  # type: ignore
        self.chat_history = result.to_input_list()  # type: ignore
        print(
            result.final_output,
            "=========================================GREEN OUTPUT",
        )
        return result.final_output


class GreenAgentExecutor(AgentExecutor):
    def __init__(self, mcp_url: str, docker_mcp_url: str = None) -> None:
        """Initialize the Green Agent Executor."""
        self.green_agent = GreenAgent(
            mcp_url=mcp_url, docker_mcp_url=docker_mcp_url
        )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task = context.current_task
        if task is None:  # first chat
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("working...", task.contextId, task.id),
        )
        reply_text = await self.green_agent.invoke(context)
        await updater.add_artifact(
            [Part(root=TextPart(text=reply_text))],
            name="response",
        )
        await updater.complete()

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")

    async def _reply(self, event_queue: EventQueue, text: str) -> None:
        await event_queue.enqueue_event(new_agent_text_message(text))
