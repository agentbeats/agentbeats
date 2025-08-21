#!/usr/bin/env python3
"""
This file contains the tools for the green agent to interact with the cybench task.

Available tools:
- setup_cybench_task: Setup the cybench task by starting the cybench server and generating the task.
- execute_command_in_container: Execute a command in the running container and return the output.
- destroy_container: Destroy the container and optionally remove the network.
"""

import os
import sys
import json
import shlex
import subprocess
import time
import docker
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import uuid

from agentbeats import tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cybench_dir = Path(__file__).resolve().parents[2] / "resources" / "cybench"

########################################################
# Asciinema functions
########################################################

import re

CSI = re.compile(
    r"\x1b\[[0-9;?]*[ -/]*[@-~]"
)  # ANSI CSI (colors, cursor moves)
OSC = re.compile(r"\x1b\][^\x07]*(?:\x07|\x1b\\)")  # OSC (title set, etc.)
CTRL = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)  # other control chars (keep \n & \t)


def extract_output_from_cast(
    cast_text: str, terminal_command: str | None = None
) -> str:
    """
    Return clean stdout/terminal text from an asciinema v2 cast.
    If `terminal_command` is provided, the echoed '$ <terminal_command>' line is removed explicitly.
    """
    if not cast_text:
        return ""

    lines = cast_text.splitlines()
    if not lines:
        return ""

    # 1) Collect all "output" events
    chunks = []
    for line in lines[1:]:  # skip header JSON
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(ev, list)
            and len(ev) >= 3
            and ev[1] == "o"
            and isinstance(ev[2], str)
        ):
            chunks.append(ev[2])

    raw = "".join(chunks)

    # 2) Strip ANSI/OSC/control noise and normalize newlines
    text = CSI.sub("", raw)
    text = OSC.sub("", text)
    text = text.replace("\r", "")
    text = CTRL.sub("", text)

    # 3) Drop prompts, echoed command, and boilerplate like "exit"
    out_lines = []
    terminal_command_line = (
        f"$ {terminal_command}".strip() if terminal_command else None
    )
    for ln in text.split("\n"):
        s = ln.strip()

        # skip empty
        if s == "":
            continue

        # skip the shell’s fancy two-line prompt (common in Kali-like images)
        if s.startswith("┌──(") or s.startswith("└─"):
            continue

        # skip generic prompt lines and echoed command
        if s == "$" or s.startswith("$ "):
            if terminal_command_line and s == terminal_command_line:
                continue
            # if you want to drop *all* "$ something" lines, keep the next line:
            continue

        # skip our termination line, if it slipped in
        if s == "exit":
            continue

        out_lines.append(ln)

    return "\n".join(out_lines).strip()


########################################################
# Cybench tools
########################################################


client = docker.from_env()
image_name = "cybench/cybench:latest"
network_name = "shared_net"
containers = {}  # Maps container_name to container object


def cleanup_existing_container(battle_id: str = None):
    """Remove existing container if it exists"""
    container_name = _get_container_name(battle_id)
    try:
        container = client.containers.get(container_name)
        container.remove(force=True)
        logger.info(f"Removed existing container: {container_name}")
        if container_name in containers:
            del containers[container_name]
    except docker.errors.NotFound:
        pass  # Container doesn't exist, which is fine


def create_network_if_needed():
    """Create shared network if it doesn't exist"""
    try:
        client.networks.get(network_name)
    except docker.errors.NotFound:
        logger.info(f"Creating Docker network: {network_name}")
        client.networks.create(network_name)


def execute_task_script(script_path: str, script_name: str):
    """Execute start_docker.sh or stop_docker.sh if they exist"""
    if os.path.isfile(script_path):
        logger.info(f"Executing {script_name} script for the task")
        try:
            subprocess.run([script_path], check=True, shell=True)
        except subprocess.CalledProcessError as e:
            logger.warning(
                f"Warning: {script_name} script failed with exit code {e.returncode}"
            )


def _sanitize_cast_env(cast_path: str) -> None:
    """
    Ensure the asciinema header's env values are strings to satisfy uploader validation.
    This rewrites only the first JSON line (header) and leaves events untouched.
    """
    try:
        with open(cast_path, "r") as f:
            lines = f.readlines()
        if not lines:
            return
        header = json.loads(lines[0])
        env_obj = header.get("env")
        if isinstance(env_obj, dict):
            # Coerce all values to strings; keep keys as-is (JSON object keys are strings)
            header["env"] = {
                str(k): (v if isinstance(v, str) else str(v))
                for k, v in env_obj.items()
            }
            lines[0] = json.dumps(header) + "\n"
            with open(cast_path, "w") as f:
                f.writelines(lines)
    except Exception:
        # Best-effort; do not fail recording if sanitization cannot complete
        pass


def extract_output_from_cast(
    cast_text: str,
    terminal_command: Optional[str] = None,
    preserve_colors: bool = True,
) -> str:
    """
    Return clean stdout/terminal text from an asciinema v2 cast.
    If `terminal_command` is provided, the echoed '$ <terminal_command>' line is removed explicitly.
    If preserve_colors is True, ANSI color codes are kept.
    """
    if not cast_text:
        return ""

    lines = cast_text.splitlines()
    if not lines:
        return ""

    # 1) Collect all "output" events
    chunks = []
    for line in lines[1:]:  # skip header JSON
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(ev, list)
            and len(ev) >= 3
            and ev[1] == "o"
            and isinstance(ev[2], str)
        ):
            chunks.append(ev[2])

    raw = "".join(chunks)

    # 2) Strip ANSI/OSC/control noise and normalize newlines
    if preserve_colors:
        # Only remove cursor positioning and screen clearing, keep color codes
        # Color codes end with 'm', so we keep those and remove others
        text = raw
        # Remove cursor movement sequences (H, A, B, C, D, etc. but NOT m)
        text = re.sub(r"\x1b\[[0-9;]*[HJKABCDEFGPQRSTU]", "", text)
        # Remove some other common non-color sequences
        text = re.sub(r"\x1b\[[0-9;]*[@]", "", text)  # Insert/delete chars
        text = OSC.sub("", text)  # Remove OSC sequences (title changes, etc.)
    else:
        # Remove all CSI sequences (including colors)
        text = CSI.sub("", raw)
        text = OSC.sub("", text)

    text = text.replace("\r", "")
    if preserve_colors:
        # Remove control chars but preserve ESC (0x1b) for color codes
        CTRL_NO_ESC = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1a\x1c-\x1f\x7f]")
        text = CTRL_NO_ESC.sub("", text)
    else:
        text = CTRL.sub("", text)

    # 3) Drop prompts, echoed command, and boilerplate like "exit"
    out_lines = []
    terminal_command_line = (
        f"$ {terminal_command}".strip() if terminal_command else None
    )
    for ln in text.split("\n"):
        s = ln.strip()

        # skip empty
        if s == "":
            continue

        # skip the shell’s fancy two-line prompt (common in Kali-like images)
        if s.startswith("┌──(") or s.startswith("└─"):
            continue

        # skip generic prompt lines and echoed command
        if s == "$" or s.startswith("$ "):
            if terminal_command_line and s == terminal_command_line:
                continue
            # if you want to drop *all* "$ something" lines, keep the next line:
            continue

        # skip our termination line, if it slipped in
        if s == "exit":
            continue

        out_lines.append(ln)

    return "\n".join(out_lines).strip()


def _check_container_running(container: str) -> None:
    """Check if a Docker container is running, raise RuntimeError if not."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format={{.State.Running}}", container],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip() != "true":
            raise RuntimeError(f"Container {container} is not running")
    except subprocess.CalledProcessError:
        raise RuntimeError(
            f"Container {container} does not exist or is not accessible"
        )


def _execute_command_simple(
    container: str,
    terminal_command: str,
    use_bash_login: bool = True,
    timeout: int = 60,
) -> Dict[str, str]:
    """Execute a command in a container without asciinema recording."""
    _check_container_running(container)

    # Prepare the command
    if use_bash_login:
        actual_terminal_command = (
            f"bash -lc '. /venv/bin/activate && {terminal_command}'"
        )
    else:
        actual_terminal_command = terminal_command

    # Execute the command
    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                container,
                "bash",
                "-c",
                actual_terminal_command,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": str(result.returncode),
        }

    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Command execution timed out after {timeout} seconds"
        )


def record_terminal_command_to_cast(
    container: str,
    terminal_command: str,
    simulate_typing: bool = True,
    cps: int = 50,
    use_bash_login: bool = True,
    timeout: int = 60,
) -> Dict[str, str]:
    """
    Start asciinema in the container, run terminal_command, record it,
    and copy the resulting .cast to the host.

    Requires: `asciinema` installed in the container.

    Returns:
        {
            "asciinema_url": str, # the url of the asciinema cast file
            "terminal_output": str, # the output of the command
        }
    """
    asciinema_path = os.path.abspath(
        os.path.join("asciinema_outputs", f"{uuid.uuid4()}.cast")
    )
    logger.info(f"Asciinema path: {asciinema_path}")
    tmp_cast = "/tmp/agent.cast"

    # Check if container is running
    _check_container_running(container)

    # Clean any existing cast file to avoid caching issues
    subprocess.run(
        ["docker", "exec", container, "rm", "-f", tmp_cast],
        capture_output=True,
    )

    # What we will "run" in the container
    actual_terminal_command = terminal_command
    if use_bash_login:
        # Make the shell run inside bash -lc <terminal_command> with venv activated so PATH/aliases/profiles are loaded.
        actual_terminal_command = (
            f"bash -lc '. /venv/bin/activate && {terminal_command}'"
        )

    if simulate_typing:
        # Create a script that simulates typing character by character
        sleep_time = 1.0 / max(1, cps)
        # For simulate_typing, we need to show the original command but run the actual command
        display_terminal_command = (
            terminal_command  # What the user sees being typed
        )
        if use_bash_login:
            exec_terminal_command = f". /venv/bin/activate && {terminal_command}"  # What actually gets executed
        else:
            exec_terminal_command = terminal_command

        # Escape the display command for safe embedding in bash, preserve newlines
        escaped_display_terminal_command = display_terminal_command.replace(
            "'", "'\"'\"'"
        )

        typing_script = f"""#!/bin/bash
export TERM=xterm-256color

# Create the typing simulation script
cat > /tmp/type_and_run.sh << 'SCRIPT_EOF'
#!/bin/bash
# Simulate typing the command
echo -n "$ "
terminal_command='{escaped_display_terminal_command}'
for ((i=0; i<${{#terminal_command}}; i++)); do
    char="${{terminal_command:$i:1}}"
    if [[ "$char" == " " ]] || [[ "$char" == $'\\n' ]]; then
        # Print spaces and newlines instantly
        echo -n "$char"
    else
        # Type non-whitespace characters with delay
        echo -n "$char"
        sleep {sleep_time}
    fi
done
echo
# Actually run the command (with venv activation if needed)
{exec_terminal_command}
SCRIPT_EOF

chmod +x /tmp/type_and_run.sh
asciinema rec -q -y {shlex.quote(tmp_cast)} --command="/tmp/type_and_run.sh"
rm -f /tmp/type_and_run.sh
"""

        # Write the typing script to the container
        script_path = "/tmp/typing_script.sh"

        # Create the script
        write_script_terminal_command = [
            "docker",
            "exec",
            "-i",
            container,
            "tee",
            script_path,
        ]
        script_proc = subprocess.run(
            write_script_terminal_command,
            input=typing_script.encode(),
            capture_output=True,
        )
        if script_proc.returncode != 0:
            raise RuntimeError(
                f"Failed to write typing script: {script_proc.stderr.decode()}"
            )

        # Make it executable
        chmod_terminal_command = [
            "docker",
            "exec",
            container,
            "chmod",
            "+x",
            script_path,
        ]
        chmod_proc = subprocess.run(
            chmod_terminal_command, capture_output=True
        )
        if chmod_proc.returncode != 0:
            raise RuntimeError(
                f"Failed to make script executable: {chmod_proc.stderr.decode()}"
            )

        # Run the script
        run_terminal_command = ["docker", "exec", container, script_path]

    else:
        # Simply record the command directly (with venv activation if needed)
        if use_bash_login:
            exec_terminal_command = (
                f". /venv/bin/activate && {terminal_command}"
            )
        else:
            exec_terminal_command = terminal_command

        # run_terminal_command = [
        #     "docker", "exec", container, "bash", "-c",
        #     f"export TERM=xterm-256color; asciinema rec -q -y {shlex.quote(tmp_cast)} --command={shlex.quote(exec_terminal_command)}"
        # ]
        run_terminal_command = [
            "docker",
            "exec",
            container,
            "bash",
            "-c",
            f"SHELL=/bin/bash TERM=xterm-256color asciinema rec -q -y {shlex.quote(tmp_cast)} --command={shlex.quote(exec_terminal_command)}",
        ]

    # Execute the recording
    try:
        result = subprocess.run(
            run_terminal_command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            logger.error(f"Command stdout: {result.stdout}")
            logger.error(f"Command stderr: {result.stderr}")
            raise RuntimeError(
                f"Recording failed with exit code {result.returncode}"
            )

        logger.info(f"Recording completed successfully")

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Recording timed out after {timeout} seconds")

    # Copy the cast file out
    try:
        os.makedirs(os.path.dirname(asciinema_path) or ".", exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory: {e}")
        raise RuntimeError(f"Failed to create directory: {e}")

    try:
        subprocess.run(
            ["docker", "cp", f"{container}:{tmp_cast}", asciinema_path],
            check=True,
        )
        logger.info(f"Successfully recorded to {asciinema_path}")
        # Sanitize header env to ensure all values are strings (required by uploader)
        _sanitize_cast_env(asciinema_path)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to copy cast file from container: {e}")
        raise RuntimeError(f"Failed to copy cast file from container: {e}")

    # Clean up the temporary script if we created one
    if simulate_typing:
        try:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    container,
                    "rm",
                    "-f",
                    "/tmp/typing_script.sh",
                ],
                capture_output=True,
            )
        except Exception as e:
            logger.error(f"Failed to cleanup typing script: {e}")
            raise RuntimeError(f"Failed to cleanup typing script: {e}")

    try:
        terminal_output = extract_output_from_cast(
            open(asciinema_path).read(), terminal_command, preserve_colors=True
        )
    except Exception as e:
        logger.error(f"Error extracting output from cast: {e}")
        raise RuntimeError(f"Error extracting output from cast: {e}")

    # Upload to asciinema
    try:
        result = subprocess.run(
            ["asciinema", "upload", asciinema_path],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        combined_output = f"{result.stdout}\n{result.stderr}".strip()

        logger.info(f"Asciinema upload result: {combined_output}")

        # Extract and print only the first URL
        match = re.search(r"(https?://[^\s]+)", combined_output)
        if match:
            asciinema_url = match.group(1) + ".cast"
            logger.info(f"Asciinema URL: {asciinema_url}")
            return {
                "asciinema_url": asciinema_url,
                "terminal_output": terminal_output,
            }
    except Exception as e:
        logger.error(f"Error uploading asciinema: {e}")
        return {
            "asciinema_url": None,
            "terminal_output": terminal_output,
        }


def _get_container_name(battle_id: str = None) -> str:
    return f"cybench_{battle_id}" if battle_id else "cybench"


@tool
def execute_command_in_container(
    battle_id: str,
    terminal_command: str,
    show_asciinema: bool = True,
    simulate_typing: bool = True,
    cps: int = 500,
    use_bash_login: bool = True,
    timeout: int = 60,
) -> Dict[str, str]:
    """
    Execute a command in a Docker container with optional asciinema recording.

    Args:
        container: Name or ID of the Docker container
        terminal_command: Command to execute

        --- for agents: don't change the following arguments ---
        show_asciinema: Whether to record with asciinema
        simulate_typing: Whether to simulate typing when recording
        cps: Characters per second for typing simulation
        use_bash_login: Whether to use bash login shell with venv activation
        timeout: Timeout in seconds for command execution

    Returns:
        Dictionary with execution results. Format depends on show_asciinema:
        - If show_asciinema=False: {"terminal_output": str}
        - If show_asciinema=True: {"asciinema_url": str, "terminal_output": str}
    """
    container = _get_container_name(battle_id)

    if show_asciinema:
        return record_terminal_command_to_cast(
            container=container,
            terminal_command=terminal_command,
            simulate_typing=simulate_typing,
            cps=cps,
            use_bash_login=use_bash_login,
            timeout=timeout,
        )
    else:
        return _execute_command_simple(
            container=container,
            terminal_command=terminal_command,
            use_bash_login=use_bash_login,
            timeout=timeout,
        )
