# -*- coding: utf-8 -*-

import os
import agentbeats as ab
import re
import base64
import subprocess

@ab.tool
def perform_action(battle_id: str) -> str:
    try:
        print("Performing action properly")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_folder = os.path.abspath(os.path.join(current_dir, ".."))
        visualwebarena_dir = os.path.join(root_folder, "wasp", "visualwebarena")
        os.chdir(visualwebarena_dir)
        
        # Get the absolute path to the Python interpreter in the virtual environment
        python_path = os.path.join(visualwebarena_dir, "venv", "bin", "python")
        
        # Set up environment variables for the virtual environment
        env = os.environ.copy()
        env['PATH'] = os.path.join(visualwebarena_dir, "venv", "bin") + ":" + env.get('PATH', '')
        env['VIRTUAL_ENV'] = os.path.join(visualwebarena_dir, "venv")
        env['PYTHONPATH'] = os.path.join(visualwebarena_dir, "venv", "lib", "python3.10", "site-packages")
                
        result = subprocess.run([
            python_path,
            "run.py",
            "--headless",
            "--slow_mo", "0",
            "--action_set_tag", "som",
            "--observation_type", "image_som",
            "--viewport_width", "1280",
            "--viewport_height", "2048",
            "--sleep_after_execution", "0.0",
            "--max_steps", "5",
            "--agent_type", "prompt",
            "--instruction_path", "../webarena_prompt_injections/configs/system_prompts/wa_p_som_cot_id_actree_3s.json",
            "--parsing_failure_th", "3",
            "--repeating_action_failure_th", "5",
            "--test_config_base_dir", "../../logs/" + battle_id + "/webarena_tasks",
            "--eval_captioning_model_device", "cpu",
            "--eval_captioning_model", "Salesforce/blip2-flan-t5-xl",
            "--captioning_model", "Salesforce/blip2-flan-t5-xl",
            "--provider", "openai",
            "--model", "gpt-4o-mini",
            "--mode", "chat",
            "--temperature", "1.0",
            "--top_p", "0.9",
            "--context_length", "0",
            "--max_tokens", "384",
            "--max_retry", "1",
            "--max_obs_length", "3840",
            "--test_start_idx", "1000",
            "--test_end_idx", "1001",
            "--result_dir", "../../logs/" + battle_id + "/agent_logs"
        ], capture_output=True, text=True, cwd=visualwebarena_dir, env=env)

        print("STDOUT: " + result.stdout)
        print("STDERR: " + result.stderr)
        
        return result.stdout

    except Exception as e:
        print(f"FAILED: The action failed: {e}")
        return f"FAILED: The action failed: {e}"

@ab.tool
def get_image(battle_id: str) -> str:
    """
    Get the last image from the HTML file and save it to the output path.
    """
    
    print("Getting the last image... (BLUE AGENT)")

    try:
        # Compute the path relative to the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # TODO: change this to use static_expose once it's implemented
        root_folder = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        html_path = os.path.join(root_folder, "scenarios", "wasp", "logs", battle_id, "agent_logs", "render_1000.html")
        static_dir = os.path.join(root_folder, 'frontend', 'webapp', 'static')
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
        return "FAILED: The image retrieval failed"


if __name__ == "__main__":
    battle_id = "b4d373ea-b5d7-47be-9182-b5812f563e83"
    perform_action(battle_id)
    # get_image(battle_id)
    print("Blue agent completed successfully")