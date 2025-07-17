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
from argparse import Namespace


@ab.tool
def prepare_prompt_environment(query: str) -> str:
    print("Preparing prompt environment... (RED AGENT)")
    
    try:
        # Change working directory to the top level of the repo
        import os
        import subprocess

        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        os.chdir(repo_root)
        result = subprocess.run(["python", "scenarios/wasp/red_agent/prep.py"], capture_output=True, text=True)
        print("RED AGENT: " + result.stdout)
        print("RED AGENT: " + result.stderr)
        return result.stdout

    except Exception as e:
        print(f"FAILED: The environment preparation failed: {e}")
        result = f"FAILED: The environment preparation failed: {e}"
    
    return result