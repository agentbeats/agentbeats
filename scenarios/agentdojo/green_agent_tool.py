# -*- coding: utf-8 -*-

import httpx
import agentbeats as ab

from uuid import uuid4
from typing import List
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    AgentCard, Message, Part, TextPart, Role, 
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    MessageSendParams,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)

@ab.tool
async def talk_to_agent(query: str, target_url: str) -> str:
    """
    Forward *query* to another A2A agent at *target_url* and stream back
    the plain-text response.
    """
    httpx_client = httpx.AsyncClient()
    resolver = A2ACardResolver(httpx_client=httpx_client, base_url=target_url)
    card: AgentCard | None = await resolver.get_agent_card(
        relative_card_path="/.well-known/agent.json"
    )
    if card is None:
        raise RuntimeError(f"Failed to resolve agent card from {target_url}")

    client = A2AClient(httpx_client=httpx_client, agent_card=card)

    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=query))],
            messageId=uuid4().hex,
            taskId=None,
        )
    )
    req = SendStreamingMessageRequest(id=str(uuid4()), params=params)
    chunks: List[str] = []

    async for chunk in client.send_message_streaming(req):
        if not isinstance(chunk.root, SendStreamingMessageSuccessResponse):
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

    return "".join(chunks).strip() or "No response from agent."
