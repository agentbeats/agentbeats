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


def extract_output_from_cast(cast_text: str, cmd: str | None = None) -> str:
    """
    Return clean stdout/terminal text from an asciinema v2 cast.
    If `cmd` is provided, the echoed '$ <cmd>' line is removed explicitly.
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
    cmd_line = f"$ {cmd}".strip() if cmd else None
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
            if cmd_line and s == cmd_line:
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



@tool
def execute_command_in_container(
    command: str,
    battle_id: str = None,
    show_terminal: bool = True,
) -> Any:
    """
    Execute a command in the container and return the output.
    If show_asciinema is True, return the asciinema v2 JSON cast (inputs + outputs).
    Always set it true.

    Returns:
        output_text: str, # this is the output of the command that an agent should focus on
    """
    container_name = _get_container_name(battle_id)
    try:
        container = client.containers.get(container_name)
        container.reload()
        if container.status != "running":
            container.start()

        # Execute the command
        exec_result = container.exec_run(
            ["/bin/sh", "-lc", command], stdout=True, stderr=True
        )
        return exec_result.output.decode("utf-8", errors="replace")
    
    except docker.errors.NotFound:
        logger.warning(
            f"Container {container_name} not found, please run a task first"
        )
        return ""
    except Exception as e:
        logger.error(f"Error executing command in container: {e}")
        return ""


# @tool
# def execute_command_in_container(
#     command: str,
#     battle_id: str = None,
#     show_asciinema: bool = True,
#     timeout_seconds: int = 120,
# ) -> Any:
#     """
#     Execute a command in the container and return the output.
#     If show_asciinema is True, return the asciinema v2 JSON cast (inputs + outputs).
#     Always set it true.

#     Returns:
#         Dict[Any, Any]: The results of the task.
#         {
#             "output_text": str, # this is the output of the command that an agent should focus on
#             "cast_text": str, # agent can ignore this
#             "asciinema_path": str, # agent can ignore this
#         }
#     """
#     import shlex
#     import socket as pysocket

#     container_name = _get_container_name(battle_id)
#     try:
#         container = client.containers.get(container_name)
#         container.reload()
#         if container.status != "running":
#             container.start()

#         # Fast path (no recording)
#         if not show_asciinema:
#             exec_result = container.exec_run(
#                 ["/bin/sh", "-lc", command], stdout=True, stderr=True
#             )
#             return exec_result.output.decode("utf-8", errors="replace")

#         # Ensure asciinema is available (pip first; apt fallback)
#         bootstrap_cmd = r"""
# set -e
# if ! command -v asciinema >/dev/null 2>&1; then
# (python3 -m pip install --no-input --upgrade pip >/dev/null 2>&1 || true)
# (python3 -m pip install --no-input asciinema >/dev/null 2>&1 || true)
# fi
# if ! command -v asciinema >/dev/null 2>&1; then
# export DEBIAN_FRONTEND=noninteractive
# (apt-get update -y >/dev/null 2>&1 && apt-get install -y asciinema >/dev/null 2>&1) || true
# fi
# command -v asciinema >/dev/null 2>&1 && echo OK || echo MISSING
# """.strip()
#         chk = container.exec_run(["/bin/sh", "-lc", bootstrap_cmd])
#         if b"MISSING" in chk.output:
#             exec_result = container.exec_run(
#                 ["/bin/sh", "-lc", command], stdout=True, stderr=True
#             )
#             return {
#                 "output_text": exec_result.output.decode(
#                     "utf-8", errors="replace"
#                 ),
#                 "cast_text": None,
#             }

#         # Prefer bash if available (nicer prompts/line editing), fallback to sh
#         has_bash = (
#             container.exec_run(
#                 [
#                     "/bin/sh",
#                     "-lc",
#                     "command -v bash >/dev/null 2>&1 && echo YES || echo NO",
#                 ]
#             )
#             .output.decode()
#             .strip()
#             == "YES"
#         )
#         shell = "/bin/bash" if has_bash else "/bin/sh"

#         # Unique cast path
#         cast_path = f"/tmp/agentbeats_{int(time.time()*1000)}.cast"

#         # Start asciinema in interactive mode (no -c). It will spawn $SHELL.
#         # We pass TERM/size, and set SHELL explicitly so asciinema uses it.
#         run_rec = (
#             f'export PS1="$ "; '
#             f"TERM=xterm SHELL={shlex.quote(shell)} "
#             f"asciinema rec {shlex.quote(cast_path)} "
#             f"--overwrite -y -q --cols 120 --rows 30 --idle-time-limit 1"
#         )

#         api = client.api
#         exec_id = api.exec_create(
#             container.id,
#             cmd=["/bin/sh", "-lc", run_rec],
#             tty=True,
#             stdin=True,  # IMPORTANT: we will type into the TTY
#             environment={"TERM": "xterm", "COLUMNS": "120", "LINES": "30"},
#         )["Id"]

#         # Attach socket (PTY) and interact: type the command, then Ctrl-D to end
#         sock = api.exec_start(exec_id, tty=True, stream=False, socket=True)
#         sock._sock.settimeout(timeout_seconds)

#         # Helper to send bytes safely
#         def send(data: bytes):
#             if not data:
#                 return
#             sock._sock.sendall(data)

#         try:
#             # Small delay to let shell start
#             import time as _t

#             _t.sleep(0.15)

#             # Optional: set a clean prompt (this input will be recorded as typed)
#             # Comment out if you don't want this line in the cast.
#             send(b'export PS1="$ "\n')
#             _t.sleep(0.05)

#             # Type the user's command exactly so it shows in the recording
#             send(command.encode("utf-8", "replace") + b"\n")

#             # Wait a bit for command to finish; you can tune this or
#             # loop-read until you detect a prompt. We keep it simple:
#             _t.sleep(0.2)

#             # End the interactive shell & stop the recording
#             # (Ctrl-D = EOT; works for bash/sh)
#             send(b"\x04")
#         except Exception:
#             pass
#         finally:
#             # Ensure remote exec is finished so Docker closes its end
#             try:
#                 for _ in range(40):
#                     info = api.exec_inspect(exec_id)
#                     if not info.get("Running", False):
#                         break
#                     _t.sleep(0.05)
#             except Exception:
#                 pass
#             # Graceful shutdown of local socket/response to avoid warnings
#             try:
#                 sock._sock.shutdown(pysocket.SHUT_RDWR)
#             except Exception:
#                 pass
#             try:
#                 sock._sock.close()
#             except Exception:
#                 pass
#             try:
#                 sock.close()
#             except Exception:
#                 pass
#             try:
#                 resp = getattr(sock, "_response", None)
#                 if resp is not None:
#                     resp.close()
#             except Exception:
#                 pass

#         # Poll for the cast file and read it
#         cast_text = ""
#         loops = max(4, int(timeout_seconds / 0.25))
#         for _ in range(loops):
#             size_res = container.exec_run(
#                 [
#                     "/bin/sh",
#                     "-lc",
#                     f"test -f {shlex.quote(cast_path)} && wc -c < {shlex.quote(cast_path)} || echo 0",
#                 ]
#             )
#             try:
#                 size = int(
#                     size_res.output.decode("utf-8", errors="replace").strip()
#                     or "0"
#                 )
#             except Exception:
#                 size = 0
#             if size > 0:
#                 cat_res = container.exec_run(
#                     ["/bin/sh", "-lc", f"cat {shlex.quote(cast_path)}"]
#                 )
#                 cast_text = cat_res.output.decode("utf-8", errors="replace")
#                 if cast_text:
#                     break
#             _t.sleep(0.25)

#         # Cleanup best-effort
#         container.exec_run(
#             [
#                 "/bin/sh",
#                 "-lc",
#                 f"rm -f {shlex.quote(cast_path)} >/dev/null 2>&1 || true",
#             ]
#         )

#         #
#         # Replace all non-alphanumeric, dot, underscore, dash with underscores
#         cast_filename = str(uuid.uuid4())
#         with open(f"{cast_filename}.cast", "w", encoding="utf-8") as f:
#             f.write(cast_text)
#         absolute_path = os.path.abspath(f"{cast_filename}.cast")
#         logger.info(f"Saved cast to: {absolute_path}")
#         output_text = extract_output_from_cast(cast_text)

#         return {
#             "output_text": output_text,
#             "cast_text": cast_text,
#             "asciinema_path": absolute_path,
#         }

#     except docker.errors.NotFound:
#         logger.warning(
#             f"Container {container_name} not found, please run a task first"
#         )
#         return ""
#     except Exception as e:
#         logger.error(f"Error executing command in container: {e}")
#         return ""


def _get_container_name(battle_id: str = None) -> str:
    return f"cybench_{battle_id}" if battle_id else "cybench"
