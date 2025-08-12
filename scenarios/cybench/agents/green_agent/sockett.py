#!/usr/bin/env python3
"""
Python equivalent of run_task.sh using Docker SDK
Runs the cybench task in a Docker container and retrieves the prompt
"""

import os
import sys
import json
import subprocess
import time
import re
import docker
from pathlib import Path
from typing import Optional, Dict, Any
import socket as pysocket  # at top of file, if not already

import json, re

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


class DockerTaskRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "cybench/cybench:latest"
        self.network_name = "shared_net"
        self.containers = {}  # Maps container_name to container object
        self.current_dir = (
            Path(__file__).resolve().parents[2] / "resources" / "cybench"
        )

    def validate_current_directory(self):
        """Validate that we're running from the cybench directory"""
        current_dir = Path.cwd().name
        if current_dir != "cybench":
            raise ValueError(
                "Error: Please run this script from the cybench directory."
            )

    def cleanup_existing_container(self, battle_id: str = None):
        """Remove existing container if it exists"""
        container_name = self._get_container_name(battle_id)
        try:
            container = self.client.containers.get(container_name)
            container.remove(force=True)
            print(f"Removed existing container: {container_name}")
            if container_name in self.containers:
                del self.containers[container_name]
        except docker.errors.NotFound:
            pass  # Container doesn't exist, which is fine

    def create_network_if_needed(self):
        """Create shared network if it doesn't exist"""
        try:
            self.client.networks.get(self.network_name)
        except docker.errors.NotFound:
            print(f"Creating Docker network: {self.network_name}")
            self.client.networks.create(self.network_name)

    def execute_task_script(self, script_path: str, script_name: str):
        """Execute start_docker.sh or stop_docker.sh if they exist"""
        if os.path.isfile(script_path):
            try:
                subprocess.run([script_path], check=True, shell=True)
            except subprocess.CalledProcessError as e:
                print(
                    f"Warning: {script_name} script failed with exit code {e.returncode}"
                )

    def parse_json_output(self, output: str) -> Optional[Dict[Any, Any]]:
        """Parse JSON output from the container logs"""
        lines = output.split("\n")
        json_start = False
        json_lines = []

        for line in lines:
            if "--- JSON OUTPUT ---" in line:
                json_start = True
                continue
            elif "--- END JSON OUTPUT ---" in line:
                break
            elif json_start:
                json_lines.append(line)

        if json_lines:
            try:
                json_content = "\n".join(json_lines)
                return json.loads(json_content)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse JSON output: {e}")

        return None

    def run_container(self, task_dir: str, battle_id: str = None) -> str:
        """Run the Docker container for the given task_dir and battle_id"""
        current_dir = self.current_dir
        volumes = {
            str(current_dir / "agent"): {"bind": "/app/agent", "mode": "ro"},
            str(current_dir / "setup_cybench_env.py"): {
                "bind": "/app/run_task.py",
                "mode": "ro",
            },
        }
        env_vars = {}
        env_file = current_dir / ".env"
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value
        if "DOCKER_NETWORK_DRIVER" not in env_vars:
            env_vars["DOCKER_NETWORK_DRIVER"] = "bridge"
        print("Running Docker container for task_dir:", task_dir)
        container_name = self._get_container_name(battle_id)
        # Build the command to run inside the container
        command = [
            "--task_dir",
            task_dir,
            # Add other default arguments here if needed
        ]
        try:
            print(f"Pulling {self.image_name} image...")
            self.client.images.pull(self.image_name)
            print("Image pulled successfully")
            print(f"Running container {container_name}...")
            container = self.client.containers.run(
                image=self.image_name,
                command=command,
                name=container_name,
                network=self.network_name,
                volumes=volumes,
                environment=env_vars,
                privileged=True,
                detach=True,
                remove=False,
                stdout=True,
                stderr=True,
                cgroupns="host",
            )
            self.containers[container_name] = container
            result = container.wait()
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            with open("/tmp/benchmark-latest.log", "w") as f:
                f.write(logs)
            # print("=" * 50)
            # print("CONTAINER LOGS:")
            # print(logs)
            # print("=" * 50)

            if result["StatusCode"] != 0:
                raise RuntimeError(
                    f"Container exited with status code {result['StatusCode']}"
                )
            return logs
        except Exception as e:
            try:
                container = self.client.containers.get(container_name)
                container.remove(force=True)
                if container_name in self.containers:
                    del self.containers[container_name]
            except:
                pass
            raise e

    def setup_cybench_task(
        self, task_dir: str, battle_id: str = None
    ) -> Dict[Any, Any]:
        """Main method to run the task and return results"""
        # self.validate_current_directory()
        if not task_dir:
            raise ValueError("task_dir argument is required")
        self.cleanup_existing_container(battle_id)
        self.create_network_if_needed()
        start_script = os.path.join(
            self.current_dir, task_dir, "start_docker.sh"
        )
        self.execute_task_script(start_script, "start_docker.sh")
        try:
            output = self.run_container(task_dir, battle_id)
            json_result = self.parse_json_output(output)
            if json_result is None:
                print(
                    "Warning: Could not parse JSON output, trying text extraction"
                )
                return {"output": output, "prompt": None}
            return json_result
        finally:
            # stop_script = os.path.join(
            #     self.current_dir, task_dir, "stop_docker.sh"
            # )
            # self.execute_task_script(stop_script, "stop_docker.sh")
            pass

    def execute_command_in_container(
        self,
        command: str,
        battle_id: str = None,
        show_asciinema: bool = False,
        timeout_seconds: int = 120,
    ) -> Any:
        import shlex
        import socket as pysocket

        container_name = self._get_container_name(battle_id)
        try:
            container = self.client.containers.get(container_name)
            container.reload()
            if container.status != "running":
                container.start()

            # Fast path (no recording)
            if not show_asciinema:
                exec_result = container.exec_run(
                    ["/bin/sh", "-lc", command], stdout=True, stderr=True
                )
                return exec_result.output.decode("utf-8", errors="replace")

            # Ensure asciinema is available (pip first; apt fallback)
            bootstrap_cmd = r"""
    set -e
    if ! command -v asciinema >/dev/null 2>&1; then
    (python3 -m pip install --no-input --upgrade pip >/dev/null 2>&1 || true)
    (python3 -m pip install --no-input asciinema >/dev/null 2>&1 || true)
    fi
    if ! command -v asciinema >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    (apt-get update -y >/dev/null 2>&1 && apt-get install -y asciinema >/dev/null 2>&1) || true
    fi
    command -v asciinema >/dev/null 2>&1 && echo OK || echo MISSING
    """.strip()
            chk = container.exec_run(["/bin/sh", "-lc", bootstrap_cmd])
            if b"MISSING" in chk.output:
                exec_result = container.exec_run(
                    ["/bin/sh", "-lc", command], stdout=True, stderr=True
                )
                return {
                    "output_text": exec_result.output.decode(
                        "utf-8", errors="replace"
                    ),
                    "cast_text": None,
                }

            # Prefer bash if available (nicer prompts/line editing), fallback to sh
            has_bash = (
                container.exec_run(
                    [
                        "/bin/sh",
                        "-lc",
                        "command -v bash >/dev/null 2>&1 && echo YES || echo NO",
                    ]
                )
                .output.decode()
                .strip()
                == "YES"
            )
            shell = "/bin/bash" if has_bash else "/bin/sh"

            # Unique cast path
            cast_path = f"/tmp/agentbeats_{int(time.time()*1000)}.cast"

            # Start asciinema in interactive mode (no -c). It will spawn $SHELL.
            # We pass TERM/size, and set SHELL explicitly so asciinema uses it.
            run_rec = (
                f'export PS1="$ "; '
                f"TERM=xterm SHELL={shlex.quote(shell)} "
                f"asciinema rec {shlex.quote(cast_path)} "
                f"--overwrite -y -q --cols 120 --rows 30 --idle-time-limit 1"
            )

            api = self.client.api
            exec_id = api.exec_create(
                container.id,
                cmd=["/bin/sh", "-lc", run_rec],
                tty=True,
                stdin=True,  # IMPORTANT: we will type into the TTY
                environment={"TERM": "xterm", "COLUMNS": "120", "LINES": "30"},
            )["Id"]

            # Attach socket (PTY) and interact: type the command, then Ctrl-D to end
            sock = api.exec_start(exec_id, tty=True, stream=False, socket=True)
            sock._sock.settimeout(timeout_seconds)

            # Helper to send bytes safely
            def send(data: bytes):
                if not data:
                    return
                sock._sock.sendall(data)

            try:
                # Small delay to let shell start
                import time as _t

                _t.sleep(0.15)

                # Optional: set a clean prompt (this input will be recorded as typed)
                # Comment out if you don't want this line in the cast.
                send(b'export PS1="$ "\n')
                _t.sleep(0.05)

                # Type the user's command exactly so it shows in the recording
                send(command.encode("utf-8", "replace") + b"\n")

                # Wait a bit for command to finish; you can tune this or
                # loop-read until you detect a prompt. We keep it simple:
                _t.sleep(0.2)

                # End the interactive shell & stop the recording
                # (Ctrl-D = EOT; works for bash/sh)
                send(b"\x04")
            except Exception:
                pass
            finally:
                # Ensure remote exec is finished so Docker closes its end
                try:
                    for _ in range(40):
                        info = api.exec_inspect(exec_id)
                        if not info.get("Running", False):
                            break
                        _t.sleep(0.05)
                except Exception:
                    pass
                # Graceful shutdown of local socket/response to avoid warnings
                try:
                    sock._sock.shutdown(pysocket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    sock._sock.close()
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
                try:
                    resp = getattr(sock, "_response", None)
                    if resp is not None:
                        resp.close()
                except Exception:
                    pass

            # Poll for the cast file and read it
            cast_text = ""
            loops = max(4, int(timeout_seconds / 0.25))
            for _ in range(loops):
                size_res = container.exec_run(
                    [
                        "/bin/sh",
                        "-lc",
                        f"test -f {shlex.quote(cast_path)} && wc -c < {shlex.quote(cast_path)} || echo 0",
                    ]
                )
                try:
                    size = int(
                        size_res.output.decode(
                            "utf-8", errors="replace"
                        ).strip()
                        or "0"
                    )
                except Exception:
                    size = 0
                if size > 0:
                    cat_res = container.exec_run(
                        ["/bin/sh", "-lc", f"cat {shlex.quote(cast_path)}"]
                    )
                    cast_text = cat_res.output.decode(
                        "utf-8", errors="replace"
                    )
                    if cast_text:
                        break
                _t.sleep(0.25)

            # Cleanup best-effort
            container.exec_run(
                [
                    "/bin/sh",
                    "-lc",
                    f"rm -f {shlex.quote(cast_path)} >/dev/null 2>&1 || true",
                ]
            )

            #
            # Replace all non-alphanumeric, dot, underscore, dash with underscores
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", command).strip("_")
            with open(f"{safe_name}.cast", "w", encoding="utf-8") as f:
                f.write(cast_text)
            absolute_path = os.path.abspath(f"{safe_name}.cast")
            print(f"Saved cast to: {absolute_path}")
            output_text = extract_output_from_cast(cast_text)
            return {
                "output_text": output_text,
                "cast_text": cast_text,
                "asciinema_path": absolute_path,
            }

        except docker.errors.NotFound:
            print(
                f"Container {container_name} not found, please run a task first"
            )
            return ""
        except Exception as e:
            print(f"Error executing command in container: {e}")
            return ""

    def destroy_container(
        self, battle_id: str = None, remove_network: bool = False
    ) -> bool:
        """
        Destroy the container and optionally remove the network.

        Args:
            battle_id: The battle_id for the container to destroy (None for default)
            remove_network: If True, also remove the shared network if no other containers are using it

        Returns:
            bool: True if container was successfully destroyed, False otherwise
        """
        container_name = self._get_container_name(battle_id)
        try:
            # Get the container
            container = self.client.containers.get(container_name)

            # Stop the container if it's running
            if container.status == "running":
                print(f"Stopping container: {container_name}")
                container.stop(timeout=10)

            # Remove the container
            print(f"Removing container: {container_name}")
            container.remove(force=True)
            print(f"Successfully destroyed container: {container_name}")

            # Optionally remove the network
            if remove_network:
                self._cleanup_network()

            if container_name in self.containers:
                del self.containers[container_name]

            return True

        except docker.errors.NotFound:
            print(
                f"Container {container_name} not found - already destroyed or never created"
            )
            return True
        except Exception as e:
            print(f"Error destroying container {container_name}: {e}")
            return False

    def _cleanup_network(self):
        """
        Remove the shared network if no other containers are using it.
        This is a helper method for destroy_container.
        """
        try:
            network = self.client.networks.get(self.network_name)

            # Check if any containers are still connected to this network
            connected_containers = network.attrs.get("Containers", {})

            if not connected_containers:
                print(f"Removing unused network: {self.network_name}")
                network.remove()
                print(f"Successfully removed network: {self.network_name}")
            else:
                print(
                    f"Network {self.network_name} still has connected containers, keeping it"
                )

        except docker.errors.NotFound:
            print(
                f"Network {self.network_name} not found - already removed or never created"
            )
        except Exception as e:
            print(
                f"Warning: Failed to remove network {self.network_name}: {e}"
            )

    def _get_container_name(self, battle_id: str = None) -> str:
        return f"cybench_{battle_id}" if battle_id else "cybench"


def main():
    """Main function to handle command line execution"""
    # Example: pass battle_id and task_dir as arguments
    battle_id = "example123"  # Replace with dynamic value as needed
    task_dir = "benchmark/hackthebox/cyber-apocalypse-2024/crypto/[Very Easy] Dynastic"
    # task_dir = "benchmark/project-sekai-ctf/sekaictf-2023/misc/just-another-pickle-jail"
    runner = DockerTaskRunner()
    try:
        print("=" * 50)
        print("Setting up cybench task...")
        results = runner.setup_cybench_task(task_dir, battle_id=battle_id)
        print("Testing command execution in container...")
        print("=" * 50)

        out = runner.execute_command_in_container(
            "pip install asciinema",
            battle_id=battle_id,
            show_asciinema=False,
        )
        print("Installed asciinema: ", out)
        print("-" * 10)

        cmds = [
            "ls -la && pwd",
            "cd /tmp/cyber-bench",
            "pwd",
            "echo 100000000000000 && echo 1000",
        ]
        for cmd in cmds:
            out = runner.execute_command_in_container(
                cmd, battle_id=battle_id, show_asciinema=True
            )
            print("-" * 10)
            print(f"{cmd} output:")
            print(out)
            print("-" * 10)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        runner.client.close()


if __name__ == "__main__":
    main()
