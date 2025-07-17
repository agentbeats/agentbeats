# -*- coding: utf-8 -*-
"""
A implementation of a green agent that follows the specification in TensorTrust
(https://arxiv.org/abs/2311.01011)
This agent hosts Blue ( defender ) vs Red ( attacker ) prompt-injection battles,
evaluates the outcome, and declares the winner.
"""

import os
import httpx
import random
import string
import agentbeats as ab
from openai import OpenAI
import sys

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
            taskId=uuid4().hex,
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

@ab.tool
def run_evaluator(query: str) -> str:
    """
    Run the evaluator script to assess the battle results.
    """
    print("Evaluator tool called from green agent.")
    
    import subprocess
    import os
    from pathlib import Path
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    
    # Path to the evaluator_final_wrapper.py script
    wrapper_script = script_dir / 'evaluator_final_wrapper.py'
    
    if not wrapper_script.exists():
        return "Error: evaluator_final_wrapper.py not found"
    
    try:
        # Run the wrapper script
        result = subprocess.run(
            [sys.executable, str(wrapper_script)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        print("Evaluator completed successfully")
        return str({"stdout": result.stdout, "stderr": result.stderr})
    except subprocess.CalledProcessError as e:
        error_msg = f"Error running evaluator: {e.stderr}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        return error_msg