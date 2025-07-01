# -*- coding:utf-8 -*-

import json
import re
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List
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
        self.tool_list = [
            self._create_reset_tool(),
        ]
        self.main_agent = Agent(
            name="Blue Agent", 
            instructions=BLUE_AGENT_PROMPT.replace("{password}", password), 
            model="o4-mini", 
            tools=self.tool_list,
        )
    
    def _create_reset_tool(self):
        """Create a reset tool for the Blue Agent."""
        @function_tool(name_override="reset_blue_agent")
        def _reset() -> str:
            """Reset the Blue Agent state."""
            self.chat_history.clear()
            print("Blue Agent state has been reset.")
            return "Blue Agent state has been reset."

        return _reset

    async def invoke(self, context) -> str: 
        """Invoke the main agent with the given context."""
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(), 
            "role": "user"
        }]

        result = await Runner.run(self.main_agent, query_ctx)
        self.chat_history = result.to_input_list()

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
            task = new_task(context.message)
            event_queue.enqueue_event(task)
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
