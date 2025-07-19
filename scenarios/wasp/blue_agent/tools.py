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
import re
import base64


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
    

@ab.tool
def get_image() -> str:
    """
    Get the last image from the HTML file and save it to the output path.
    """
    
    print("Getting the last image... (BLUE AGENT)")

    try:
        # Compute the path relative to the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        html_path = os.path.join(repo_root, 'wasp', 'webarena_prompt_injections', 'testdir-with-output', '0', 'agent_logs', 'render_1000.html')
        static_dir = os.path.join(repo_root, 'webapp', 'static')
        output_filename = 'blue_image.png'
        output_path = os.path.join(static_dir, output_filename)

        # Regex to match base64 image data in <img> tags
        img_data_re = re.compile(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)')

        last_b64 = None

        # Efficiently scan for the last base64 image
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                for match in img_data_re.finditer(line):
                    last_b64 = match.group(1)
        
        if last_b64 is None:
            print("No base64 image found.")
            return None
        else:
            # Ensure the static directory exists
            os.makedirs(static_dir, exist_ok=True)
            # Decode and save the image
            img_bytes = base64.b64decode(last_b64)
            with open(output_path, 'wb') as out:
                out.write(img_bytes)
            print(f'Last image extracted and saved to {output_path}')
            return output_filename
        
    except Exception as e:
        print(f"FAILED: The image retrieval failed: {e}")
        return None
    

if __name__ == "__main__":
    print("The image filename is: ", get_image())