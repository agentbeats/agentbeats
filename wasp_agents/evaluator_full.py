# Implement the evaluator final
import subprocess
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of wasp_agents)
project_root = os.path.dirname(script_dir)

# Hardcoded output directory structure (matching prep.py pattern)
output_dir = os.path.join(project_root, 'wasp/webarena_prompt_injections/testdir-with-output')
output_dir_idx = 0

if output_dir[-1] == '/':
    output_dir = output_dir + str(output_dir_idx) + '/'
else:
    output_dir = output_dir + '/' + str(output_dir_idx) + '/'

# Define subdirectories
log_dir = os.path.join(output_dir, 'agent_logs')
task_dir = os.path.join(output_dir, 'webarena_tasks')
attacker_task_dir = os.path.join(output_dir, 'webarena_tasks_attacker')

print(f"Output directory: {output_dir}")
print(f"Log directory: {log_dir}")
print(f"Task directory: {task_dir}")
print(f"Attacker task directory: {attacker_task_dir}")

# Change to the webarena_prompt_injections/scripts directory before running the command
scripts_dir = os.path.join(project_root, 'wasp/webarena_prompt_injections/scripts')
os.chdir(scripts_dir)

# Run step-by-step evaluation
print("Running step-by-step evaluation...")
step_by_step_command = [
    'bash',
    'step3_run_evaluators.sh',
    output_dir,
    'webarena'  # output format
]

subprocess.run(step_by_step_command)

# Change back to wasp_agents folder after execution
os.chdir(script_dir)
