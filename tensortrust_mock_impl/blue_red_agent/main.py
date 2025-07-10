# -*- coding: utf-8 -*-

"""
A implementation of a blue agent that follows the specification in TensorTrust (https://arxiv.org/abs/2311.01011)
This agent is designed to act as a defender from prompt injection attacks, which generates inpenetrable prompts and can reset its state when needed.
"""

import yaml
import json
import argparse
import uvicorn
from typing import Dict, List

from agents import Agent, Runner

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_task, new_agent_text_message
from a2a.types import AgentCard, TaskState, Part, TextPart


class AgentBeatsExecutor(AgentExecutor):
    def __init__(self, agent_card_json: dict) -> None:
        # Initialize the agent
        self.agent_card_json = agent_card_json
        self.chat_history: List[Dict[str, str]] = []

        # construct AGENT_PROMPT with password and agent_card_json
        AGENT_PROMPT = str(agent_card_json["description"])
        AGENT_PROMPT += "\n\n"
        AGENT_PROMPT += str(agent_card_json["skills"])

        self.main_agent = Agent(
            name=agent_card_json["name"], 
            instructions=AGENT_PROMPT, 
            model="o4-mini", 
        )

    async def invoke(self, context) -> str: 
        """[USER LOGIC HERE] Invoke the main agent with the given context."""
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(), 
            "role": "user"
        }]

        result = await Runner.run(self.main_agent, query_ctx)
        self.chat_history = result.to_input_list()

        print(result.final_output)
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


def main() -> None:
    # parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run the Blue Agent (Defender) server with a configurable port.",
    )
    parser.add_argument(
        "--agent-card",
        type=str,
        default="tensortrust_mock_impl/blue_agent/agent_card.yaml",
        help="Path to the agent card YAML file.",
    )
    args = parser.parse_args()

    # read agent card from YAML file
    with open(args.agent_card, "r") as f:
        agent_card_json = json.dumps(yaml.safe_load(f))
    agent_card = AgentCard(**agent_card_json)

    # create the A2A Starlette application with the agent card and request handler
    application = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=AgentBeatsExecutor(agent_card_json=agent_card_json),
            task_store=InMemoryTaskStore(),
        ),
    )
    uvicorn.run(application.build(), host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
