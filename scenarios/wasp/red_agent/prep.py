# The script is run from the top level of the agentbeats project

from argparse import Namespace
import subprocess
import os

def inject_prompt():
    args = Namespace(render=True, slow_mo=0, action_set_tag='som', observation_type='image_som', current_viewport_only=False, viewport_width=1280, viewport_height=2048, save_trace_enabled=False, sleep_after_execution=0.0, max_steps=15, agent_type='prompt', instruction_path='wasp/webarena_prompt_injections/configs/system_prompts/wa_p_som_cot_id_actree_3s.json', parsing_failure_th=3, repeating_action_failure_th=5, test_config_base_dir='wasp/webarena_prompt_injections/testdir-with-output/0/webarena_tasks', eval_captioning_model_device='cpu', eval_captioning_model='Salesforce/blip2-flan-t5-xl', captioning_model='Salesforce/blip2-flan-t5-xl', provider='openai', model='gpt-4o-mini', mode='chat', temperature=1.0, top_p=0.9, context_length=0, max_tokens=384, stop_token=None, max_retry=1, max_obs_length=3840, test_start_idx=1000, test_end_idx=1001, result_dir='wasp/webarena_prompt_injections/testdir-with-output/0/agent_logs')

    # Get the current working directory (should be the project root)
    project_root = os.getcwd()
    
    # Verify we're in the right directory by checking for key files
    if not os.path.exists('wasp/webarena_prompt_injections'):
        raise FileNotFoundError("This script must be run from the top level of the agentbeats project")

    output_dir = os.path.join(project_root, 'wasp/webarena_prompt_injections/testdir-with-output')
    output_dir_idx = 0

    if output_dir[-1] == '/':
        output_dir = output_dir + str(output_dir_idx) + '/'
    else:
        output_dir = output_dir + '/' + str(output_dir_idx) + '/'

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Change to the webarena_prompt_injections/scripts directory before running the command
    scripts_dir = os.path.join(project_root, 'wasp/webarena_prompt_injections/scripts')
    os.chdir(scripts_dir)

    # Activate the virtual environment
    venv_path = os.path.join(project_root, 'wasp/visualwebarena/venv')
    if not os.path.exists(venv_path):
        raise FileNotFoundError(f"Virtual environment not found at {venv_path}")
    
    # Get the Python executable from the virtual environment
    if os.name == 'nt':  # Windows
        python_executable = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:  # Unix/Linux/macOS
        python_executable = os.path.join(venv_path, 'bin', 'python')
    
    if not os.path.exists(python_executable):
        raise FileNotFoundError(f"Python executable not found at {python_executable}")

    command = [
        'bash',
        'step1_setup_prompt_injections.sh',
        output_dir,
        args.model,
        os.path.join(project_root, 'wasp/webarena_prompt_injections/configs/system_prompts/wa_p_som_cot_id_actree_3s.json'),
        os.path.join(project_root, 'wasp/webarena_prompt_injections/configs/experiment_config_reduced.raw.json'),
        '0',
        'goal_hijacking_plain_text',
        'webarena'
    ]

    # Set environment variables to use the virtual environment
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = venv_path
    env['PATH'] = os.path.join(venv_path, 'bin') + os.pathsep + env.get('PATH', '')
    
    # Run the command with the virtual environment activated
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    # Change back to project root after execution
    os.chdir(project_root)

    return str({"stdout": result.stdout, "stderr": result.stderr})

if __name__ == "__main__":
    inject_prompt()
