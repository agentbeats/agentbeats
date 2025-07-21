# -*- coding:utf-8 -*-

import asyncio
from typing import List
from uuid import uuid4
import httpx
import agentbeats
import logging

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

httpx_client: httpx.AsyncClient = httpx.AsyncClient()


async def _make_client(base_url: str) -> A2AClient:
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url,
    )
    card: AgentCard | None = await resolver.get_agent_card(
        relative_card_path="/.well-known/agent.json"
    )
    if card is None:
        raise RuntimeError(f"Failed to resolve agent card from {base_url}")
    return A2AClient(httpx_client=httpx_client, agent_card=card)


@agentbeats.tool()
async def _talk_to_agent(
    query: str, target_url: str, timeout_seconds: float = 120.0
) -> str:
    logging.info(f"Talking to agent at {target_url} with query: {query}")
    logging.info(f"Timeout: {timeout_seconds}")
    client = await _make_client(target_url)
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
    except asyncio.TimeoutError:
        logging.warning(
            f"[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds."
        )
        return "[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds."
    ans = "".join(chunks).strip() or "No response from agent."
    logging.info(ans)
    return ans
