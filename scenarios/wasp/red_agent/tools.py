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
import re
import base64

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
import shutil



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

@ab.tool
def get_image() -> str:
    """
    Get the last image from the HTML file and save it to the output path.
    """
    
    print("Getting the last image... (RED AGENT)")

    try:
        # Compute the path relative to the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        image_path = os.path.join(repo_root, 'wasp', 'webarena_prompt_injections', 'testdir-with-output', '0', 'gitlab_environment_setup.png')
        static_dir = os.path.join(repo_root, 'webapp', 'static')
        output_filename = 'gitlab_environment_setup.png'

        # Ensure the static directory exists
        os.makedirs(static_dir, exist_ok=True)
        # Copy the image from image_path to static_dir/output_filename
        dest_path = os.path.join(static_dir, output_filename)
        shutil.copyfile(image_path, dest_path)
        print(f"Image copied to {dest_path}")
        return output_filename
    
    except Exception as e:
        print(f"FAILED: The image retrieval failed: {e}")
    
    return None

if __name__ == "__main__":
    prepare_prompt_environment("a")
