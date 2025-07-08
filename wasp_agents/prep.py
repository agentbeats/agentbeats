# The script is run from /Users/galgantar/Documents/UCB/agentbeats/wasp_agents

from argparse import Namespace
import subprocess
import os


args = Namespace(render=True, slow_mo=0, action_set_tag='som', observation_type='image_som', current_viewport_only=False, viewport_width=1280, viewport_height=2048, save_trace_enabled=False, sleep_after_execution=0.0, max_steps=15, agent_type='prompt', instruction_path='../wasp/webarena_prompt_injections/configs/system_prompts/wa_p_som_cot_id_actree_3s.json', parsing_failure_th=3, repeating_action_failure_th=5, test_config_base_dir='../wasp/webarena_prompt_injections/testdir-with-output/0/webarena_tasks', eval_captioning_model_device='cpu', eval_captioning_model='Salesforce/blip2-flan-t5-xl', captioning_model='Salesforce/blip2-flan-t5-xl', provider='openai', model='gpt-4o-mini', mode='chat', temperature=1.0, top_p=0.9, context_length=0, max_tokens=384, stop_token=None, max_retry=1, max_obs_length=3840, test_start_idx=1000, test_end_idx=1004, result_dir='../wasp/webarena_prompt_injections/testdir-with-output/0/agent_logs')

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of wasp_agents)
project_root = os.path.dirname(script_dir)

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

subprocess.run(command)

# Change back to wasp_agents folder after execution
os.chdir(script_dir)
