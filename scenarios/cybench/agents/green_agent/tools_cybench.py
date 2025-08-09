#!/usr/bin/env python3
"""
Python equivalent of run_task.sh using Docker SDK
Runs the cybench task in a Docker container and retrieves the prompt
"""

import os
import sys
import json
import argparse
import subprocess
import docker
from pathlib import Path
from typing import Optional, Dict, Any


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
        print("script_path", script_path, os.path.isfile(script_path))

        if os.path.isfile(script_path):
            print(f"Executing {script_name} script for the task")
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
            print("=" * 50)
            print("CONTAINER LOGS:")
            print(logs)
            print("=" * 50)

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
        self, command: str, battle_id: str = None
    ) -> str:
        """Execute a command in the running container and return the output"""
        container_name = self._get_container_name(battle_id)
        try:
            container = self.client.containers.get(container_name)

            # Check if container is running
            if container.status != "running":
                print(
                    f"Container {container_name} is not running, restarting it..."
                )
                container.start()

            # Execute command in the running container
            exec_result = container.exec_run(command, stdout=True, stderr=True)
            output = exec_result.output.decode("utf-8")

            return output

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
    # task_dir = "benchmark/hackthebox/cyber-apocalypse-2024/crypto/[Very Easy] Dynastic"
    task_dir = "benchmark/project-sekai-ctf/sekaictf-2023/misc/just-another-pickle-jail"
    runner = DockerTaskRunner()
    try:
        results = runner.setup_cybench_task(task_dir, battle_id=battle_id)
        print("Testing command execution in container...")
        ls_output = runner.execute_command_in_container(
            "ls -la /tmp/cyber-bench", battle_id=battle_id
        )
        print(ls_output)
        prompt_key = (
            "prompt"
            if "prompt" in results
            else (
                "challenge_prompt" if "challenge_prompt" in results else None
            )
        )
        if prompt_key:
            print("\n" + "=" * 50)
            print("EXTRACTED PROMPT:")
            print("=" * 50)
            print(results[prompt_key])
            print("=" * 50)
            print(results["task"]["subtasks"])
            return results[prompt_key]
        else:
            print("Warning: No prompt found in results")
            return None
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
