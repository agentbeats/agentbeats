# -*- coding: utf-8 -*-

"""
A implementation of a blue agent that follows the specification in TensorTrust (https://arxiv.org/abs/2311.01011)
This agent is designed to act as a defender from prompt injection attacks, which generates inpenetrable prompts and can reset its state when needed.
"""

from typing import Dict, List, Any, Optional

from agents import Agent, Runner
from agents.mcp import MCPServerSse

from a2a.server.tasks import TaskUpdater
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_task, new_agent_text_message
from a2a.types import Part, TextPart, TaskState

class AgentBeatsExecutor(AgentExecutor):
    def __init__(self, agent_card_json: Dict[str, Any], 
                        mcp_list: Optional[List[MCPServerSse]] = None, 
                        tool_list: Optional[List[Any]] = None):
        """ (Shouldn't be called directly) 
            Initialize the AgentBeatsExecutor with the MCP URL and agent card JSON. """
        self.agent_card_json = agent_card_json
        self.chat_history: List[Dict[str, str]] = []

        self.mcp_list = mcp_list
        self.tool_list = tool_list
        
        # construct self.AGENT_PROMPT with agent_card_json
        self.AGENT_PROMPT = str(agent_card_json["description"])
        self.AGENT_PROMPT += "\n\n"
        self.AGENT_PROMPT += str(agent_card_json["skills"])

        self.main_agent = Agent(
            name=agent_card_json["name"],
            instructions=self.AGENT_PROMPT,
            model="o4-mini",
            tools=self.tool_list,
            mcp_servers=self.mcp_list,
        )

    @classmethod
    async def create(
        cls, 
        agent_card_json: Dict[str, Any],
        mcp_url_list: Optional[List[str]] = None,
        tool_list: Optional[List[Any]] = None,
    ) -> "AgentBeatsExecutor":
        """Asynchronous factory method to create a agent executor instance."""
        if mcp_url_list:
            mcp_server_list = [MCPServerSse(
                params={"url": mcp_url},
                cache_tools_list=True,
            ) for mcp_url in mcp_url_list]
            for mcp_server in mcp_server_list:
                await mcp_server.connect()
        else:
            mcp_server_list = None

        instance = cls(agent_card_json, mcp_server_list, tool_list)

        return instance

    async def invoke(self, context: RequestContext) -> str:
        """Run a single turn of conversation through *self._main_agent*."""
        # Build contextual chat input for the runner
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(),
            "role": "user",
        }]

        result = await Runner.run(self.main_agent, query_ctx, max_turns=30)
        self.chat_history = result.to_input_list()
        return result.final_output

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
        reply_text = await self.main_agent.invoke(context)

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
