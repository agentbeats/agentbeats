# -*- coding: utf-8 -*-

import os
import agentbeats as ab
import re
import base64
import subprocess
import shutil



@ab.tool
def prepare_prompt_environment(battle_id: str) -> str:
    try:
        max_retries = 3
        for _ in range(max_retries):
            print("Preparing environment properly")
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_folder = os.path.abspath(os.path.join(current_dir, ".."))

            os.chdir(root_folder)

            result = subprocess.run([
                "wasp/visualwebarena/venv/bin/python",
                "wasp/webarena_prompt_injections/prompt_injector.py",
                "--config", "wasp/webarena_prompt_injections/configs/experiment_config_reduced.raw.json",
                "--gitlab-domain", "http://ec2-18-224-83-14.us-east-2.compute.amazonaws.com:8023",
                "--reddit-domain", "http://ec2-18-224-83-14.us-east-2.compute.amazonaws.com:9999",
                "--model", "gpt-4o-mini",
                "--system_prompt", "wasp/webarena_prompt_injections/configs/system_prompts/wa_p_som_cot_id_actree_3s.json",
                "--output-dir", "logs/" + battle_id,
                "--user_goal_idx", "0",
                "--injection_format", "goal_hijacking_plain_text",
                "--output-format", "webarena",
                "--headless"
            ], capture_output=True, text=True)

            print("STDOUT: " + result.stdout)
            print("STDERR: " + result.stderr)

            if "Failed to end up at the expected URL" in result.stdout:
                print("Retrying...")
            else:
                return result.stdout

    except Exception as e:
        print(f"FAILED: The environment preparation failed: {e}")
        return f"FAILED: The environment preparation failed: {e}"

    return "FAILED: The environment preparation failed after 3 attempts"

@ab.tool
def get_image(battle_id: str) -> str:
    """
    Get the last image from the HTML file and save it to the output path.
    """
    
    print("Getting the last image... (RED AGENT)")

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # TODO: change this to use static_expose once it's implemented
        root_folder = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        image_path = os.path.join(root_folder, 'scenarios', 'wasp', 'logs', battle_id, 'gitlab_environment_setup.png')
        static_dir = os.path.join(root_folder, 'frontend', 'webapp', 'static')
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
    battle_id = "b4d373ea-b5d7-47be-9182-b5812f563e83"
    # prepare_prompt_environment(battle_id)
    get_image(battle_id)
    print("Red agent completed successfully")