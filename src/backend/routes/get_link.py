import subprocess
import re
import sys

asciinema_path = "/Users/lukeleeai/agentbeats_project/agentbeats/scenarios/cybench/bash_-lc_for_i_in_1_2_3_4_5_do_echo_Hello_world_sleep_0.8_done.cast"

# Upload the asciinema file and capture both stdout and stderr
result = subprocess.run(
    ["asciinema", "upload", asciinema_path],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=False,
)

combined_output = f"{result.stdout}\n{result.stderr}".strip()

# Extract and print only the first URL
match = re.search(r"(https?://[^\s]+)", combined_output)
if match:
    print(match.group(1))
else:
    print("No URL found in output:", combined_output, file=sys.stderr)
    sys.exit(1)
