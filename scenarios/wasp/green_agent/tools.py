# -*- coding: utf-8 -*-

import os
import httpx
import agentbeats as ab
import time
import json
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
import sys

def auto_login() -> str:
    """
    Auto logins the user to the gitlab instance.
    """
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_folder = os.path.abspath(os.path.join(current_dir, ".."))
        visualwebarena_dir = os.path.join(root_folder, "wasp", "visualwebarena")
        
        # Get the absolute path to the Python interpreter in the virtual environment
        python_path = os.path.join(visualwebarena_dir, "venv", "bin", "python")
        
        # Set environment variables for the subprocess
        env = os.environ.copy()

        os.chdir(visualwebarena_dir)
        
        subprocess.run([
            "mkdir",
            "-p",
            "./.auth"
        ])
        
        # Run auto_login.py
        result = subprocess.run([
            python_path,
            "browser_env/auto_login.py",
        ], capture_output=True, text=True, cwd=visualwebarena_dir, env=env)
        
        print("STDOUT (AUTO LOGIN): " + result.stdout, file=sys.__stdout__, flush=True)
        print("STDERR (AUTO LOGIN): " + result.stderr, file=sys.__stdout__, flush=True)
        
        # Check if the command failed
        if result.returncode != 0:
            return f"FAILED: Auto login command failed with return code {result.returncode}. Error: {result.stderr}"
        
        return "Auto login completed"
        
    except Exception as e:
        print(f"FAILED: The auto login failed: {e}", file=sys.__stdout__, flush=True)
        print("STDERR (AUTO LOGIN): " + result.stderr, file=sys.__stdout__, flush=True)
        return f"FAILED: The auto login failed: {e}"


@ab.tool
def run_evaluator() -> str:
    try:
        # first we auto login
        auto_login()
        
        battle_id = ab.get_battle_id()
        
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
        
        print("STDOUT (EVALUATOR OF ATTACKER TASK): " + result.stdout, file=sys.__stdout__, flush=True)
        print("STDERR (EVALUATOR OF ATTACKER TASK): " + result.stderr, file=sys.__stdout__, flush=True)

        result_2 = subprocess.run([
            python_path,
            "evaluator_final_step.py",
            "--log-folder", "../../logs/" + battle_id + "/agent_logs",
            "--task-folder", "../../logs/" + battle_id + "/webarena_tasks",
            "--headless",
            "--slow-mo", "0"
        ], capture_output=True, text=True, cwd=visualwebarena_dir)

        print("STDOUT (EVALUATOR OF USER TASK): " + result_2.stdout, file=sys.__stdout__, flush=True)
        print("STDERR (EVALUATOR OF USER TASK): " + result_2.stderr, file=sys.__stdout__, flush=True)
        
        return result.stdout + result_2.stdout
    
    except Exception as e:
        print("STDOUT (EVALUATOR OF USER TASK): " + result_2.stdout, file=sys.__stdout__, flush=True)
        print("STDERR (EVALUATOR OF USER TASK): " + result_2.stderr, file=sys.__stdout__, flush=True)

        print(f"FAILED: The evaluator failed: {e}", file=sys.__stdout__, flush=True)
        return f"FAILED: The evaluator failed: {e}"

@ab.tool
def reset_battle() -> str:
    try:
        battle_id = ab.get_battle_id()

        print("Resetting battle properly for battle_id: " + battle_id + " with auth token: " + os.environ.get('RESET_AUTH_TOKEN'), file=sys.__stdout__, flush=True)

        return "Battle reset successfully" # TODO: Remove this

        # Reset the server
        import requests
        response = requests.post(
            "http://ec2-18-224-83-14.us-east-2.compute.amazonaws.com:5001/reset-server",
            headers={"Authorization": f"Bearer {os.environ.get('RESET_AUTH_TOKEN')}"},
        )
        print("Reset server response:", response.text, file=sys.__stdout__, flush=True)

        print("Waiting for 80 seconds for gitlab docker to start up")
        # Wait for 80 seconds for gitlab docker to start up
        time.sleep(80)

        return "Battle reset successfully"
    
    except Exception as e:
        print(f"FAILED: The reset battle failed: {e}", file=sys.__stdout__, flush=True)
        return f"FAILED: The reset battle failed: {e}"
