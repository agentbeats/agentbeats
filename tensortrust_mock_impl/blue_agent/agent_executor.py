# -*- coding:utf-8 -*-

import json
import re
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Sequence
from agents import Agent, Runner, function_tool, RunContextWrapper

from prompt import BLUE_AGENT_PROMPT

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart
from a2a.utils import new_task, new_agent_text_message


class BlueAgent:
    def __init__(self, password) -> None:
        """Initialize the Blue Agent with its prompt and tools."""
        self.chat_history: List[Dict[str, str]] = []
<<<<<<< HEAD
=======
        self.tool_list: Sequence = [
            self._create_reset_tool(),
        ]
>>>>>>> 6abbeb94761b815c93665b408e81453b5cb3872b
        self.main_agent = Agent(
            name="Blue Agent", 
            instructions=BLUE_AGENT_PROMPT.replace("{password}", password), 
            model="o4-mini", 
<<<<<<< HEAD
=======
            tools=list(self.tool_list),  # type: ignore
>>>>>>> 6abbeb94761b815c93665b408e81453b5cb3872b
        )

    async def invoke(self, context) -> str: 
        """Invoke the main agent with the given context."""
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(), 
            "role": "user"
        }]

        result = await Runner.run(self.main_agent, query_ctx)  # type: ignore
        self.chat_history = result.to_input_list()  # type: ignore

        return result.final_output


class BlueAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        """Initialize the Blue Agent Executor."""
        self._password = "p@ssw0rd"
        self.blue_agent = BlueAgent(password=self._password)

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # make / get current task
        task = context.current_task
        if task is None: # first chat
<<<<<<< HEAD
            task = new_task(context.message)
=======
            task = new_task(context.message)  # type: ignore
>>>>>>> 6abbeb94761b815c93665b408e81453b5cb3872b
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        # push "working now" status
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("working...", task.contextId, task.id),
        )

        # await llm response
        reply_text = await self.blue_agent.invoke(context)

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
