# -*- coding: utf-8 -*-

import os
import agentbeats as ab
import re
import base64
import subprocess
from PIL import Image
import io
from agentbeats.utils import static_expose


@ab.tool
def perform_action(battle_id: str) -> str:
    try:
        print("Performing action properly")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_folder = os.path.abspath(os.path.join(current_dir, ".."))
        visualwebarena_dir = os.path.join(
            root_folder, "wasp", "visualwebarena"
        )
        os.chdir(visualwebarena_dir)

        # Get the absolute path to the Python interpreter in the virtual environment
        python_path = os.path.join(visualwebarena_dir, "venv", "bin", "python")

        # Set up environment variables for the virtual environment
        env = os.environ.copy()
        env["PATH"] = (
            os.path.join(visualwebarena_dir, "venv", "bin")
            + ":"
            + env.get("PATH", "")
        )
        env["VIRTUAL_ENV"] = os.path.join(visualwebarena_dir, "venv")
        env["PYTHONPATH"] = os.path.join(
            visualwebarena_dir, "venv", "lib", "python3.10", "site-packages"
        )

        result = subprocess.run(
            [
                python_path,
                "run.py",
                "--headless",
                "--slow_mo",
                "0",
                "--action_set_tag",
                "som",
                "--observation_type",
                "image_som",
                "--viewport_width",
                "1280",
                "--viewport_height",
                "2048",
                "--sleep_after_execution",
                "0.0",
                "--max_steps",
                "5",
                "--agent_type",
                "prompt",
                "--instruction_path",
                "../webarena_prompt_injections/configs/system_prompts/wa_p_som_cot_id_actree_3s.json",
                "--parsing_failure_th",
                "3",
                "--repeating_action_failure_th",
                "5",
                "--test_config_base_dir",
                "../../logs/" + battle_id + "/webarena_tasks",
                "--eval_captioning_model_device",
                "cpu",
                "--eval_captioning_model",
                "Salesforce/blip2-flan-t5-xl",
                "--captioning_model",
                "Salesforce/blip2-flan-t5-xl",
                "--provider",
                "openai",
                "--model",
                "gpt-4o-mini",
                "--mode",
                "chat",
                "--temperature",
                "1.0",
                "--top_p",
                "0.9",
                "--context_length",
                "0",
                "--max_tokens",
                "384",
                "--max_retry",
                "1",
                "--max_obs_length",
                "3840",
                "--test_start_idx",
                "1000",
                "--test_end_idx",
                "1001",
                "--result_dir",
                "../../logs/" + battle_id + "/agent_logs",
            ],
            capture_output=True,
            text=True,
            cwd=visualwebarena_dir,
            env=env,
        )

        print("STDOUT: " + result.stdout)
        print("STDERR: " + result.stderr)

        return result.stdout

    except Exception as e:
        print(f"FAILED: The action failed: {e}")
        return f"FAILED: The action failed: {e}"


@ab.tool
def create_gif(battle_id: str) -> str:
    """
    Extract all base64-encoded images from render_1000.html and create a GIF or video.

    Args:
        battle_id (str): The battle ID to find the HTML file

    Returns:
        str: The filename of the created GIF/video
    """
    try:
        print(f"Extracting images and creating GIF for battle_id: {battle_id}")

        # Compute paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_folder = os.path.abspath(
            os.path.join(current_dir, "..", "..", "..")
        )
        html_path = os.path.join(
            root_folder,
            "scenarios",
            "wasp",
            "logs",
            battle_id,
            "agent_logs",
            "render_1000.html",
        )

        # Check if HTML file exists
        if not os.path.exists(html_path):
            return f"FAILED: HTML file not found at {html_path}"

        # Regex to match base64 image data in <img> tags
        img_data_re = re.compile(r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)")

        images = []
        print("Reading HTML file and extracting images...")

        # Read HTML file and extract all base64 images
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                for match in img_data_re.finditer(line):
                    try:
                        b64_data = match.group(1)
                        img_bytes = base64.b64decode(b64_data)
                        img = Image.open(io.BytesIO(img_bytes))
                        images.append(img)
                        print(
                            f"Extracted image {len(images)} from line {line_num}"
                        )
                    except Exception as e:
                        print(
                            f"Failed to decode image from line {line_num}: {e}"
                        )
                        continue

        if not images:
            return "FAILED: No images found in HTML file"

        print(f"Successfully extracted {len(images)} images")

        print("Creating GIF")

        # Create battle logs directory path
        battle_logs_dir = os.path.join(
            root_folder, "scenarios", "wasp", "logs", battle_id, "agent_logs"
        )

        # Ensure battle logs directory exists
        os.makedirs(battle_logs_dir, exist_ok=True)

        # Save GIF in battle logs
        local_filename = f"blue_agent_gif_{battle_id}.gif"
        local_path = os.path.join(battle_logs_dir, local_filename)

        # Save as GIF
        if len(images) == 1:
            images[0].save(local_path, "GIF")
        else:
            # Save as animated GIF with 500ms delay between frames
            images[0].save(
                local_path,
                "GIF",
                save_all=True,
                append_images=images[1:],
                duration=500,
                loop=0,
            )

        print(f"GIF saved locally in battle logs: {local_path}")

        # Upload to GCP using static_expose
        try:
            gcp_url = static_expose(
                local_path, f"blue_agent_gif_{battle_id}.gif"
            )
            print(f"GIF uploaded to GCP: {gcp_url}")

            return gcp_url

        except Exception as upload_error:
            print(f"Failed to upload GIF to GCP: {upload_error}")
            return f"FAILED: GCP upload failed: {upload_error}"

    except Exception as e:
        print(f"FAILED: Image extraction and GIF creation failed: {e}")
        return f"FAILED: Image extraction and GIF creation failed: {e}"


if __name__ == "__main__":
    battle_id = "b4d373ea-b5d7-47be-9182-b5812f563e83"
    perform_action(battle_id)
    # get_image(battle_id)
    print(create_gif(battle_id))
    print("Blue agent completed successfully")
