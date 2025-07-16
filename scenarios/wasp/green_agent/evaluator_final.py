# Implement the evaluator final
import subprocess
import os

# Get the project root directory (assuming script is called from project root)
project_root = os.getcwd()

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
    os.path.join(scripts_dir, 'run_final_evaluator_only.sh'),
    output_dir,
    'webarena'  # output format
]

result = subprocess.run(step_by_step_command, capture_output=True, text=True)

print("stdout", result.stdout)
print("stderr", result.stderr)

# Change back to project root after execution
os.chdir(project_root)
