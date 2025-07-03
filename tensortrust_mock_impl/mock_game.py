# -*- coding: utf-8 -*-

"""
Mock TensorTrust game orchestration script.

Steps:
1. Send reset signal to blue launcher (localhost:8000).
2. Send reset to red launcher (localhost:9000).
3. Send reset to green launcher (localhost:10000).
4. Tell green agent (at localhost:10001) to 'start battle' via A2A.
"""

import asyncio
from uuid import uuid4
from typing import AsyncGenerator

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

# Launcher URLs
BLUE_LAUNCHER_URL = "http://localhost:8000"
RED_LAUNCHER_URL = "http://localhost:9000"
GREEN_LAUNCHER_URL = "http://localhost:10000"

# Green agent service
GREEN_AGENT_BASE_URL = "http://localhost:10001"
PUBLIC_CARD_PATH = "/.well-known/agent.json"

RESET_RED_BLUE_PAYLOAD = {"signal": "reset"}
RESET_GREEN_PAYLOAD = {
    "signal": "reset",
    "extra_args": {
        "blue-agent-url": "http://localhost:8001",
        "red-agent-url": "http://localhost:9001",
        "mcp-url": "http://localhost:11000",
        "battle-id": uuid4().hex,
    },
}


async def send_reset(url: str, payload: dict) -> None:
    """POST a reset signal to *url*."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
    print(f"[reset] sent to {url} -> {resp.status_code}")
    return resp.json()


async def stream_agent_response(
    client: A2AClient, user_text: str
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

        # Assistant tokens
        if isinstance(event, TaskArtifactUpdateEvent):
            for p in event.artifact.parts:
                if isinstance(p.root, TextPart):
                    yield p.root.text
        # Final status update
        elif isinstance(event, TaskStatusUpdateEvent):
            msg = event.status.message
            if msg:
                for p in msg.parts:
                    if isinstance(p.root, TextPart):
                        yield p.root.text


async def main() -> None:
    # Step 1–3: Reset launchers
    blue_result = await send_reset(BLUE_LAUNCHER_URL + "/reset", payload=RESET_RED_BLUE_PAYLOAD)
    red_result = await send_reset(RED_LAUNCHER_URL + "/reset", payload=RESET_RED_BLUE_PAYLOAD)
    green_result = await send_reset(GREEN_LAUNCHER_URL + "/reset", payload=RESET_GREEN_PAYLOAD)

    print(f"\n=== Reset Results ===\nBlue: {blue_result}\nRed: {red_result}\nGreen: {green_result}")

    # Step 4: Send "start battle" to green agent via A2A
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=GREEN_AGENT_BASE_URL)
        card: AgentCard | None = await resolver.get_agent_card(
            relative_card_path=PUBLIC_CARD_PATH
        )
        if card is None:
            raise RuntimeError("Failed to resolve agent card.")

        client = A2AClient(httpx_client=httpx_client, agent_card=card)

        print("\n=== Start Battle ===")
        async for text in stream_agent_response(client, "start battle"):
            print(text, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
