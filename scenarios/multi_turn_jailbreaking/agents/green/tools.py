# -*- coding:utf-8 -*-

import asyncio
import time
from typing import List
from uuid import uuid4
from pathlib import Path
import httpx
from agentbeats import tool
import logging
from collections import defaultdict


import json


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


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

battle_start_times = defaultdict(float)
battle_cumulative_times = defaultdict(float)


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


@tool
async def talk_to_red_or_blue_agent(
    query: str, target_url: str, battle_id: str, timeout_seconds: float = 120.0
) -> str:
    """Talk to a red or blue agent at the given URL with a query. Tracks cumulative time for the battle."""
    logging.info(
        f"Talking to agent at {target_url} with query: {query} for battle {battle_id}"
    )
    logging.info(f"Timeout: {timeout_seconds}")

    # Check if battle has started, if not start the stopwatch
    if (
        battle_id not in battle_start_times
        or battle_start_times[battle_id] == 0
    ):
        battle_start_times[battle_id] = time.time()
        logging.info(f"Starting stopwatch for battle {battle_id}")
    else:
        logging.info(
            f"Continuing existing battle {battle_id} (started at {battle_start_times[battle_id]})"
        )

    client = await _make_client(target_url)
    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=query))],
            messageId=uuid4().hex,
            taskId=None,  # Let the red agent create a new task
        )
    )
    req = SendStreamingMessageRequest(id=str(uuid4()), params=params)
    chunks: List[str] = []
    message_start_time = time.time()
    try:

        async def stream_reply():
            async for chunk in client.send_message_streaming(req):
                # Log the chunk for debugging
                logging.debug(f"Received chunk: {chunk}")

                if not isinstance(
                    chunk.root, SendStreamingMessageSuccessResponse
                ):
                    continue
                event = chunk.root.result

                # Handle TaskArtifactUpdateEvent (final response)
                if isinstance(event, TaskArtifactUpdateEvent):
                    for p in event.artifact.parts:
                        if isinstance(p.root, TextPart):
                            chunks.append(p.root.text)
                # Handle TaskStatusUpdateEvent (status messages)
                elif isinstance(event, TaskStatusUpdateEvent):
                    msg = event.status.message
                    if msg:
                        for p in msg.parts:
                            if isinstance(p.root, TextPart):
                                chunks.append(p.root.text)
                # Handle any other event type that might contain text
                else:
                    # Try to extract text from any other event type
                    if hasattr(event, "message") and event.message:
                        for p in event.message.parts:
                            if isinstance(p.root, TextPart):
                                chunks.append(p.root.text)
                    elif hasattr(event, "text"):
                        chunks.append(str(event.text))
                    elif hasattr(event, "content"):
                        chunks.append(str(event.content))

        await asyncio.wait_for(stream_reply(), timeout=timeout_seconds)
        message_end_time = time.time()
        message_elapsed = message_end_time - message_start_time

        # Update cumulative time for this battle
        battle_cumulative_times[battle_id] += message_elapsed

        ans = "".join(chunks).strip() or "No response from agent."
        logging.info(ans)
        logging.info(f"Message response time: {message_elapsed:.2f} seconds")
        logging.info(
            f"Battle {battle_id} cumulative time: {battle_cumulative_times[battle_id]:.2f} seconds"
        )

        return f"{ans}\n[Message response time: {message_elapsed:.2f} seconds]\n[Battle cumulative time: {battle_cumulative_times[battle_id]:.2f} seconds]"
    except asyncio.TimeoutError:
        # Still count timeout towards cumulative time
        message_end_time = time.time()
        message_elapsed = message_end_time - message_start_time
        battle_cumulative_times[battle_id] += message_elapsed

        logging.warning(
            f"[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds."
        )
        logging.info(
            f"Battle {battle_id} cumulative time: {battle_cumulative_times[battle_id]:.2f} seconds"
        )
        return f"[Timeout] No response from agent at {target_url} after {timeout_seconds} seconds.\n[Battle cumulative time: {battle_cumulative_times[battle_id]:.2f} seconds]"


@tool
async def get_attack_cumulative_time(battle_id: str) -> str:
    """Get the cumulative time the red agent has spent attacking the target."""
    if battle_id not in battle_cumulative_times:
        return f"No communication time recorded for battle {battle_id}"

    cumulative_time = battle_cumulative_times[battle_id]
    start_time = battle_start_times.get(battle_id, 0)

    if start_time == 0:
        return f"Battle {battle_id} has no recorded start time"

    current_time = time.time()
    total_battle_time = current_time - start_time

    return (
        f"Battle {battle_id} stats:\n"
        # f"- Cumulative red agent attack time: {cumulative_time:.2f} seconds\n"
        f"- Red agent attack time: {total_battle_time:.2f} seconds\n"
    )


@tool
async def reset_battle_timing(battle_id: str) -> str:
    """Reset the timing data for a specific battle."""
    if battle_id in battle_start_times:
        del battle_start_times[battle_id]
    if battle_id in battle_cumulative_times:
        del battle_cumulative_times[battle_id]

    return f"Timing data reset for battle {battle_id}"


########################################################
# Conversation history tools
########################################################


@tool
async def read_conversation_history(battle_id: str) -> str:
    """Read the conversation history between the red agent and the blue agent."""
    history_path = (
        Path(__file__).parent.parent / f"logs/conversation_{battle_id}.jsonl"
    )

    entries = []
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    entries.append(entry)
    except FileNotFoundError:
        return f"No conversation history found for battle {battle_id}."
    except Exception as e:
        return f"Error reading conversation history: {e}"

    if not entries:
        return f"No conversation history found for battle {battle_id}."

    # Format the conversation
    formatted = [
        f"Query: {entry.get('query', '?')}\nResponse: {entry.get('response', '?')}\n"
        for entry in entries
    ]
    return "\n".join(formatted)
