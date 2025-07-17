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
import sys


@ab.tool
def perform_action(query: str) -> str:
    print("BLUE AGENT: Perform action tool called from blue agent.")
    
    import subprocess
    import os
    from pathlib import Path
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    
    # Path to the perform_action_wrapper.py script
    wrapper_script = script_dir / 'perform_action_wrapper.py'
    
    if not wrapper_script.exists():
        return "Error: perform_action_wrapper.py not found"
    
    try:
        # Run the wrapper script
        result = subprocess.run(
            [sys.executable, str(wrapper_script)],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        print("Blue agent action completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = f"BLUE AGENT: Error running blue agent action: {e.stderr}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        return error_msg