# -*- coding: utf-8 -*-

"""
A test client for the blue agent that follows the specification in TensorTrust (https://arxiv.org/abs/2311.01011).
This client is designed to interact with the blue agent, testing its ability to generate prompts that defend against prompt injection attacks and reset its state when needed.
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

AGENT_URL = "http://localhost:8000"
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
        resolver = A2ACardResolver(httpx_client=httpx_client, 
                                   base_url=AGENT_URL)
        card = await resolver.get_agent_card()
        if card is None:
            raise RuntimeError("Failed to resolve agent card.")

        client = A2AClient(httpx_client=httpx_client, agent_card=card)

        # -------- Tooluse test --------
        async for text in stream_agent_response(client, 
            "please use helloworld_tool give me the greeting message string"):
            print(text, end="", flush=True)

        # -------- MCP Server --------
        async for text in stream_agent_response(client, 
            "please use your mcp server to echo this test message: 'Hello world, beasts!'"):
            print(text, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(test_plain_message())
