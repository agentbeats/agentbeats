# -*- coding: utf-8 -*-

import os
import agentbeats as ab

from agentbeats.utils import static_expose
import re
import base64
import subprocess
import shutil
from datetime import datetime, timedelta
import sys
import json

@ab.tool
def prepare_prompt_environment() -> str: 
    try:
        battle_id = ab.get_battle_id()

        max_retries = 3
        for _ in range(max_retries):
            print("Preparing environment properly")
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_folder = os.path.abspath(os.path.join(current_dir, ".."))

            os.chdir(root_folder)

            result = subprocess.run([
                "wasp/visualwebarena/venv/bin/python",
                "wasp/webarena_prompt_injections/prompt_injector.py",  
                "--gitlab-domain", os.getenv("GITLAB"),
                "--reddit-domain", os.getenv("REDDIT"),
                "--model", "gpt-4o-mini",
                "--output-dir", "logs/" + battle_id,
                "--output-format", "webarena",
                "--headless",
                
                # system prompt in AgentBeats pipeline is defined in the blue agent itself
                # "--system_prompt", "wasp/webarena_prompt_injections/configs/system_prompts/wa_p_som_cot_id_actree_3s.json",
                
                # Goal index in the AgentBeats pipeline is defined in the blue agent itself
                # "--user_goal_idx", "0",
                
                # ATTACK CONFIGURATION
                # You can try adding more injections here
                "--config", "wasp/webarena_prompt_injections/configs/experiment_config.raw.json",
                # 0 based index of the injection to inject (there are 21 injections available in wasp/webarena_prompt_injections/configs/experiment_config.raw.json)
                "--injection-index", "2",
                # Injection formats are: generic_plain_text, generic_url_injection, goal_hijacking_plain_text, goal_hijacking_url_injection - you are welcome to add new ones
                "--injection_format", "goal_hijacking_plain_text",
            ], capture_output=True, text=True)

            print("STDOUT: " + result.stdout, file=sys.__stdout__, flush=True)
            print("STDERR: " + result.stderr, file=sys.__stdout__, flush=True)

            injection_log = os.path.join(root_folder, 'logs', battle_id, 'webarena_tasks', '1000.json')
            with open(injection_log, 'r') as f:
                data = json.load(f)
            issue_number = data['start_url'].split('/')[-1]
            print("The created issue number is: " + issue_number, file=sys.__stdout__, flush=True)

            if "Failed to end up at the expected URL" in result.stdout:
                print("Retrying...")
            else:
                return result.stdout + "The created issue number is: " + issue_number

    except Exception as e:
        print(f"FAILED: The environment preparation failed: {e}", file=sys.__stdout__, flush=True)
        return f"FAILED: The environment preparation failed: {e}"

    return "FAILED: The environment preparation failed after 3 attempts"

@ab.tool
def get_image() -> str:
    try:
        battle_id = ab.get_battle_id()
        print("Getting the last image... (RED AGENT)")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_folder = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        image_path = os.path.join(root_folder, 'scenarios', 'wasp', 'logs', battle_id, 'gitlab_environment_setup.png')
        
        # Use static_expose to upload to GCP bucket
        public_url = static_expose(image_path, f"gitlab_environment_setup_{battle_id}.png", battle_id)

        print("Public URL: " + public_url, file=sys.__stdout__, flush=True)
        
        if public_url.startswith("ERROR") or public_url.startswith("GCP Error"):
            print(f"FAILED: The image upload failed: {public_url}", file=sys.__stdout__, flush=True)
            return None
        
        print(f"Image uploaded successfully: {public_url}")
        return public_url
    
    except Exception as e:
        print(f"FAILED: The image retrieval failed: {e}", file=sys.__stdout__, flush=True)
    
    return None
