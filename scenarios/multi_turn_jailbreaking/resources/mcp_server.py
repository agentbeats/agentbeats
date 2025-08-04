# -*- coding: utf-8 -*-

import logging
from fastmcp import FastMCP
import requests
from pathlib import Path
from datetime import datetime
import os
import json
from typing import List
import asyncio
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

# Configure logging once
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
logger.propagate = False
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("[%(levelname)s] [%(asctime)s] %(message)s")
)
logger.addHandler(handler)

server = FastMCP(
    "Open MCP for AgentBeats Battle Arena",
    host="0.0.0.0",
    port=9003,
)

BACKEND_URL = "http://localhost:9000"
DEBUG_MODE = True

httpx_client: httpx.AsyncClient = httpx.AsyncClient()


async def _make_client(base_url: str) -> A2AClient:
    """Create an A2A client for the given agent URL."""
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


def save_conversation_history(
    battle_id: str, query: str, response: str
) -> None:
    """Save a single query/response pair to a JSONL file."""
    history_entry = {
        "query": query,
        "response": response,
    }
    history_path = (
        Path(__file__).parent.parent / f"logs/conversation_{battle_id}.jsonl"
    )
    logging.info(f"Saving conversation history to {history_path}")
    try:
        with open(history_path, "a", encoding="utf-8") as f:  # "a" for append
            json.dump(history_entry, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logging.warning(f"Could not write history file: {e}")


@server.tool()
async def talk_to_blue_agent(
    agent_url: str, query: str, battle_id: str
) -> str:
    """
    Send a query to the agent and return the response.

    Args:
        agent_url: The URL of the agent to communicate with
        query: The query to send to the agent
        battle_id: The battle ID for saving conversation history

    Returns:
        str: The response text from the agent or an error message
    """
    logging.info(f"Talking to agent at {agent_url}")

    try:
        # Create an A2A client for the agent
        client = await _make_client(agent_url)

        # Prepare the streaming message request
        params = MessageSendParams(
            message=Message(
                role=Role.user,
                parts=[Part(TextPart(text=query))],
                messageId=uuid4().hex,
                taskId=None,  # Let the agent create a new task
            )
        )
        req = SendStreamingMessageRequest(id=str(uuid4()), params=params)

        # Collect response chunks
        chunks: List[str] = []

        async for chunk in client.send_message_streaming(req):
            if not isinstance(chunk.root, SendStreamingMessageSuccessResponse):
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
                if hasattr(event, "message") and event.message:
                    for p in event.message.parts:
                        if isinstance(p.root, TextPart):
                            chunks.append(p.root.text)
                elif hasattr(event, "text"):
                    chunks.append(str(event.text))
                elif hasattr(event, "content"):
                    chunks.append(str(event.content))

        response_text = "".join(chunks).strip() or "No response from agent."

        # Save conversation history if battle_id is provided
        save_conversation_history(battle_id, query, response_text)

        return response_text

    except Exception as e:
        error_msg = (
            f"[Error] Failed to communicate with agent at {agent_url}: {e}"
        )
        logging.error(error_msg)
        return error_msg


@server.tool()
def get_agent_urls(battle_id: str) -> dict:
    """
    Fetch the battle from the backend and return a dictionary mapping agent_id to their URL.
    """
    try:
        resp = requests.get(f"{BACKEND_URL}/battles/{battle_id}", timeout=10)
        resp.raise_for_status()
        battle = resp.json()
        agent_urls = {}

        # Opponents
        for op in battle.get("opponents", []):
            op_id = op.get("agent_id")
            if op_id:
                agent_resp = requests.get(
                    f"{BACKEND_URL}/agents/{op_id}", timeout=10
                )
                if agent_resp.status_code == 200:
                    agent = agent_resp.json()
                    url = agent.get("register_info", {}).get("agent_url")
                    if url:
                        agent_urls[op.get("name")] = url
        return agent_urls
    except Exception as e:
        return {
            "error": f"Error fetching agent URLs for battle {battle_id}: {e}"
        }


@server.tool()
def update_battle_process(
    battle_id: str,
    message: str,
    reported_by: str,
    detail: dict = None,
    markdown_content: str = None,
) -> str:
    """
    Log battle process updates to backend API and console.

    This tool records intermediate events and progress during a battle, helping track
    what each participant is doing and how the battle is evolving.

    Args:
        battle_id (str): Unique identifier for the battle session
        message (str): Simple, human-readable description of what happened
                      Example: "guardrailGenerator defense prompt success" or "red agent launched attack"
        detail (dict): Structured data containing specific details about the event
                      Can include prompts, responses, configurations, or any relevant data
                      Example: {"prompt": "You are a helpful assistant...", "tool": "xxxTool"}
        reported_by (str): The role/agent that triggered this event
                          Example: "guardrailGenerator", "red_agent", "blue_agent", "evaluator"
        markdown_content (str): Optional markdown content for rich text display, and image rendering

    Returns:
        str: Status message indicating where the log was recorded

    Example usage in multi-turn jailbreaking game:
        - message: "Red agent sent X to blue agent. The strategy is Y."
        - markdown_content: "```blue agent response```"
        - reported_by: "red_agent"
    """
    # logger.info("Battle %s: %s", battle_id, info)

    # Prepare event data for backend API
    event_data = {
        "is_result": False,
        "message": message,
        "reported_by": reported_by,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if detail:
        event_data["detail"] = detail

    if markdown_content:
        event_data["markdown_content"] = markdown_content
    try:
        # Call backend API
        response = requests.post(
            f"{BACKEND_URL}/battles/{battle_id}",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 204:
            logger.info(
                "Successfully logged to backend for battle %s", battle_id
            )
            return "logged to backend"
        else:
            logger.error(
                "Failed to log to backend for battle %s: %s",
                battle_id,
                response.text,
            )
            # Fallback to local file logging
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"[INFO] [{timestamp}] {message}\n"
            with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
                f.write(line)
            return "logged locally (backend failed)"

    except requests.exceptions.RequestException as e:
        logger.error(
            "Network error when logging to backend for battle %s: %s",
            battle_id,
            str(e),
        )
        # Fallback to local file logging
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[INFO] [{timestamp}] {message}\n"
        with open(f"{battle_id}.log", "a", encoding="utf-8") as f:
            f.write(line)
        return "logged locally (network error)"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Sec-Bench MCP server with a configurable port.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9003,
        help="TCP port for the HTTP server to listen on (default: 9002)",
    )
    args = parser.parse_args()
    server.run(
        transport="sse",
        host="0.0.0.0",
        port=args.port,
        log_level="ERROR",
    )
