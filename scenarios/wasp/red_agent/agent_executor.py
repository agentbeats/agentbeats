# -*- coding:utf-8 -*-

import json
import re
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Sequence
from agents import Agent, Runner, function_tool, RunContextWrapper

from prompt import RED_AGENT_PROMPT

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart
from a2a.utils import new_task, new_agent_text_message


class RedAgent:
    def __init__(self) -> None:
        """Initialize the Red Agent with its prompt and tools."""
        self.chat_history: List[Dict[str, str]] = []
        
        # Create tools list
        self.tool_list = [
            self._create_environment_prep_tool(),
        ]
        
        self.main_agent = Agent(
            name="Red Agent", 
            instructions=RED_AGENT_PROMPT, 
            model="o4-mini", 
            tools=self.tool_list,
        )

    def _create_environment_prep_tool(self):
        @function_tool(name_override="environment_prep")
        def _environment_prep(query: str) -> str:
            print("Environment prep tool called from red agent.")
            
            from prep import prep_environment
            prep_environment()
            print("Environment prepared by red agent.")
            return "Environment prepared by red agent."
        return _environment_prep

    async def invoke(self, context) -> str: 
        """Invoke the main agent with the given context."""
        
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(), 
            "role": "user"
        }]

        result = await Runner.run(self.main_agent, query_ctx)  # type: ignore
        self.chat_history = result.to_input_list()  # type: ignore

        print(result.final_output)

        return result.final_output


class RedAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        """Initialize the Red Agent Executor."""
        self.red_agent = RedAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # make / get current task
        task = context.current_task
        if task is None: # first chat
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
