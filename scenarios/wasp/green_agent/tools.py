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
import time

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
import subprocess

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
def run_evaluator(battle_id: str) -> str:
    try:
        print("Running evaluator properly")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        visualwebarena_dir = os.path.join(repo_root, "wasp", "visualwebarena")
        os.chdir(visualwebarena_dir)
        
        # Get the absolute path to the Python interpreter in the virtual environment
        python_path = os.path.join(visualwebarena_dir, "venv", "bin", "python")

        result = subprocess.run([
            python_path,
            "evaluator_final_step.py",
            "--log-folder", "../webarena_prompt_injections/testdir-with-output/" + battle_id + "/agent_logs",
            "--task-folder", "../webarena_prompt_injections/testdir-with-output/" + battle_id + "/webarena_tasks_attacker",
            "--format", "webarena"
        ], capture_output=True, text=True, cwd=visualwebarena_dir)
        
        print("STDOUT (EVALUATOR OF ATTACKER TASK): " + result.stdout)
        print("STDERR (EVALUATOR OF ATTACKER TASK): " + result.stderr)

        result_2 = subprocess.run([
            python_path,
            "evaluator_final_step.py",
            "--log-folder", "../webarena_prompt_injections/testdir-with-output/" + battle_id + "/agent_logs",
            "--task-folder", "../webarena_prompt_injections/testdir-with-output/" + battle_id + "/webarena_tasks",
        ], capture_output=True, text=True, cwd=visualwebarena_dir)

        print("STDOUT (EVALUATOR OF USER TASK): " + result_2.stdout)
        print("STDERR (EVALUATOR OF USER TASK): " + result_2.stderr)
        
        return result.stdout + result_2.stdout
    
    except Exception as e:
        print(f"FAILED: The evaluator failed: {e}")
        return f"FAILED: The evaluator failed: {e}"

@ab.tool
def reset_battle(battle_id: str) -> str:
    try:
        print("Resetting battle properly for battle_id: " + battle_id)

        # Reset the server
        import requests
        response = requests.post("http://ec2-18-224-83-14.us-east-2.compute.amazonaws.com:5001/reset-server")
        print("Reset server response:", response.text)

        print("Waiting for 80 seconds for gitlab docker to start up")
        # Wait for 80 seconds for gitlab docker to start up
        time.sleep(80)

        return "Battle reset successfully"
    
    except Exception as e:
        print(f"FAILED: The reset battle failed: {e}")
        return f"FAILED: The reset battle failed: {e}"

if __name__ == "__main__":
    battle_id = "b4d373ea-b5d7-47be-9182-b5812f563e83"
    run_evaluator(battle_id)