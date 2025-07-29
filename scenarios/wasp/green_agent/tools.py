# -*- coding: utf-8 -*-

import os
import httpx
import agentbeats as ab
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
        root_folder = os.path.abspath(os.path.join(current_dir, ".."))
        visualwebarena_dir = os.path.join(root_folder, "wasp", "visualwebarena")
        os.chdir(visualwebarena_dir)
        
        # Get the absolute path to the Python interpreter in the virtual environment
        python_path = os.path.join(visualwebarena_dir, "venv", "bin", "python")

        result = subprocess.run([
            python_path,
            "evaluator_final_step.py",
            "--log-folder", "../../logs/" + battle_id + "/agent_logs",
            "--task-folder", "../../logs/" + battle_id + "/webarena_tasks_attacker",
            "--format", "webarena",
            "--headless",
            "--slow-mo", "0"
        ], capture_output=True, text=True, cwd=visualwebarena_dir)
        
        print("STDOUT (EVALUATOR OF ATTACKER TASK): " + result.stdout)
        print("STDERR (EVALUATOR OF ATTACKER TASK): " + result.stderr)

        result_2 = subprocess.run([
            python_path,
            "evaluator_final_step.py",
            "--log-folder", "../../logs/" + battle_id + "/agent_logs",
            "--task-folder", "../../logs/" + battle_id + "/webarena_tasks",
            "--headless",
            "--slow-mo", "0"
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
        return "Battle reset successfully" # TODO: Remove this
        print("Resetting battle properly for battle_id: " + battle_id + " with auth token: " + os.environ.get('RESET_AUTH_TOKEN'))

        # Reset the server
        import requests
        response = requests.post(
            "http://ec2-18-224-83-14.us-east-2.compute.amazonaws.com:5001/reset-server",
            headers={"Authorization": f"Bearer {os.environ.get('RESET_AUTH_TOKEN')}"},
        )
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
    # run_evaluator(battle_id)
    reset_battle(battle_id)