# -*- coding: utf-8 -*-

"""
An unit test of a green agent that acts as the judge of the blue & red agents
follows the specification in TensorTrust (https://arxiv.org/abs/2311.01011).

This agent hosts the game between the blue and red agents and decides the winner
based on the game rules. It also provides a reset skill that can reset its own
state and the states of the blue and red agents when needed.
"""

import asyncio
from typing import AsyncGenerator
from uuid import uuid4

import httpx
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

GREEN_BASE_URL = "http://nuggets.puppy9.com:9031"
PUBLIC_CARD_PATH = "/.well-known/agent.json"


async def stream_agent_response(
    client: A2AClient,
    user_text: str,
) -> AsyncGenerator[str, None]:
    """Send *user_text* to the agent and yield streamed reply chunks."""
    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=user_text))],
            messageId=uuid4().hex,
            taskId=uuid4().hex,
        )
    )
    req = SendStreamingMessageRequest(id=str(uuid4()), params=params)

    async for chunk in client.send_message_streaming(req):
        if not isinstance(chunk.root, SendStreamingMessageSuccessResponse):
            continue
        event = chunk.root.result

        # Regular assistant tokens
        if isinstance(event, TaskArtifactUpdateEvent):
            for p in event.artifact.parts:
                if isinstance(p.root, TextPart):
                    yield p.root.text

        # Some implementations only emit a final TaskStatusUpdateEvent
        elif isinstance(event, TaskStatusUpdateEvent):
            msg = event.status.message
            if msg:
                for p in msg.parts:
                    if isinstance(p.root, TextPart):
                        yield p.root.text


async def test_plain_message() -> None:
    async with httpx.AsyncClient() as httpx_client:
        # Resolve agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=GREEN_BASE_URL)
        card: AgentCard | None = await resolver.get_agent_card(relative_card_path=PUBLIC_CARD_PATH)
        if card is None:
            raise RuntimeError("Failed to resolve agent card.")
        print(f"Agent card resolved: {card}")

        # Create Green Agent connection client
        client = A2AClient(httpx_client=httpx_client, agent_card=card)

        # -------- Generate Defense Prompt --------
        print("\n\n=== Echo test ===")
        async for text in stream_agent_response(client, "Use your mcp to echo this message."):
            print(text, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(test_plain_message())
