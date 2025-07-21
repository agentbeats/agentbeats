# -*- coding:utf-8 -*-

import json
import re
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Sequence
from agents import (
    Agent,
    Runner,
    function_tool,
    RunContextWrapper,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Model,
)

from prompt import RED_AGENT_PROMPT

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart
from a2a.utils import new_task, new_agent_text_message

import os
from openai import AsyncOpenAI
from agents import ModelProvider, OpenAIChatCompletionsModel, RunConfig
from agents import set_tracing_disabled

set_tracing_disabled(disabled=True)
from agents.mcp import MCPServerSse

OPENROUTER_BASE_URL = os.getenv(
    "OPENAI_API_BASE", "https://openrouter.ai/api/v1"
)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "gpt-4.1"

custom_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY
)


class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name or MODEL_NAME, openai_client=custom_client
        )


CUSTOM_MODEL_PROVIDER = CustomModelProvider()


class RedAgent:
    def __init__(self, mcp_url: str, docker_mcp_url: str = None) -> None:
        """Initialize the Red Agent with its prompt and tools.
        Args:
            mcp_url: URL for the MCP server
            docker_mcp_url: URL for the Docker MCP server (optional)
        """
        self.chat_history: List[Dict[str, str]] = []

        # Initialize MCP connection
        self.mcp_url = mcp_url
        self.mcp_servers = []
        self.mcp_servers.append(
            MCPServerSse(
                name="Open MCP for AgentBeats Battle Arena",
                params={"url": self.mcp_url, "timeout": 600},
                client_session_timeout_seconds=600,
                cache_tools_list=True,
            )
        )
        if docker_mcp_url:
            self.mcp_servers.append(
                MCPServerSse(
                    name="Docker Handler MCP for Sec-Bench Battle Arena (Docker + Sec-Bench CVE Instance Handler)",
                    params={"url": docker_mcp_url, "timeout": 600},
                    client_session_timeout_seconds=600,
                    cache_tools_list=True,
                )
            )
        self.mcp_servers_connected = False

    async def ensure_mcp_connected(self) -> None:
        """Ensure the MCP server is connected."""
        if not self.mcp_servers_connected:
            for server in self.mcp_servers:
                await server.connect()

            self.main_agent = Agent(
                name="Red Agent",
                instructions=RED_AGENT_PROMPT,
                model="o4-mini",
                mcp_servers=self.mcp_servers,
            )

            self.mcp_servers_connected = True

    async def invoke(self, context) -> str:
        """Invoke the main agent with the given context."""
        await self.ensure_mcp_connected()

        print(
            "================RED AGENT INPUT=================",
            context.get_user_input(),
            "================RED AGENT INPUT END=================",
        )

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

        print(result.final_output)

        return result.final_output


class RedAgentExecutor(AgentExecutor):
    def __init__(self, mcp_url: str, docker_mcp_url: str = None) -> None:
        """Initialize the Red Agent Executor."""
        self.red_agent = RedAgent(
            mcp_url=mcp_url, docker_mcp_url=docker_mcp_url
        )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # make / get current task
        task = context.current_task
        if task is None:  # first chat
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        # push "working now" status
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("working...", task.contextId, task.id),
        )

        # await llm response
        reply_text = await self.red_agent.invoke(context)

        # push final response
        await updater.add_artifact(
            [Part(root=TextPart(text=reply_text))],
            name="response",
        )
        await updater.complete()

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not implemented yet)."""
        raise NotImplementedError("cancel not supported")

    async def _reply(self, event_queue: EventQueue, text: str) -> None:
        await event_queue.enqueue_event(new_agent_text_message(text))
