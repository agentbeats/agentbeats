# -*- coding: utf-8 -*-
import os
import logging
import subprocess
import docker
from pathlib import Path

from utils.paths import (
    POC_SAVE_DIR,
    CYBERGYM_SERVER_DATA_DIR,
    CYBERGYM_TASK_DIR,
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)
CYBERGYM_PATH = os.path.join(PROJECT_ROOT, "external", "cybergym")
POC_SAVE_DIR = os.path.join(CYBERGYM_PATH, "poc_save_dir")
CYBERGYM_SERVER_DATA_DIR = os.path.join(CYBERGYM_PATH, "cybergym_data", "data")
CYBERGYM_TASK_DIR = os.path.join(CYBERGYM_PATH, "test_task_folder2")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("testing_agent.log"),
        logging.StreamHandler(),
    ],
)


# Docker connection settings
DOCKER_SOCKET_PATHS = [
    str(
        Path.home() / ".docker/run/docker.sock"
    ),  # macOS Docker Desktop path (confirmed working)
    "/var/run/docker.sock",  # Standard Linux path
    str(Path.home() / ".docker/desktop/docker.sock"),  # Alternative macOS path
]

DOCKER_IMAGES = ["cybergym/oss-fuzz-base-runner", "n132/arvo"]

DOCKER_BATTLE_CONTAINERS: dict[str, dict[str, str]] = {}


def start_cybergym_server(
    port: int = 8666,
) -> str:
    logging.info(f"Starting Cybergym server on port {port}")
    logging.info(f"POC_SAVE_DIR: {POC_SAVE_DIR}")
    logging.info(f"CYBERGYM_SERVER_DATA_DIR: {CYBERGYM_SERVER_DATA_DIR}")
    cmd = [
        "source venv/bin/activate",
        "&&",
        "python",
        "-m",
        "cybergym.server",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--log_dir",
        POC_SAVE_DIR,
        "--db_path",
        os.path.join(POC_SAVE_DIR, "poc.db"),
        "--cybergym_oss_fuzz_path",
        os.path.join(CYBERGYM_SERVER_DATA_DIR, "oss-fuzz"),
    ]
    cmd_str = " ".join(cmd)
    logging.info(f"Running command: {cmd_str}")
    process = subprocess.Popen(cmd_str, shell=True)
    logging.info(f"Cybergym server started with PID: {process.pid}")
    logging.info(f"--------------------------------")
    return process.pid


def generate_cybergym_task(task_id: str = "arvo:368") -> str:
    OUT_DIR = CYBERGYM_TASK_DIR
    CYBERGYM_DATA_DIR = CYBERGYM_SERVER_DATA_DIR
    cmd = [
        "source venv/bin/activate",
        "&&",
        "python",
        "-m",
        "cybergym.task.gen_task",
        "--task-id",
        task_id,
        "--out-dir",
        OUT_DIR,
        "--data-dir",
        CYBERGYM_DATA_DIR,
        "--server",
        f"http://host.docker.internal:8666",
        "--difficulty",
        "level1",
    ]
    cmd_str = " ".join(cmd)
    logging.info(f"Running command: {cmd_str}")
    result = subprocess.run(
        cmd_str, capture_output=True, text=True, shell=True
    )
    logging.info(f"stdout: {result.stdout.strip()}")
    logging.info(f"stderr: {result.stderr.strip()}")
    logging.info(f"Return code: {result.returncode}")
    return f"stdout: {result.stdout}\nstderr: {result.stderr}"


def get_docker_client():
    """Get a Docker client using available connection methods."""
    for socket_path in DOCKER_SOCKET_PATHS:
        if os.path.exists(socket_path):
            try:
                return docker.DockerClient(base_url=f"unix://{socket_path}")
            except Exception:
                continue
    try:
        return docker.from_env()
    except Exception as e:
        raise Exception(
            f"Could not connect to Docker daemon. Is Docker running? Error: {e}"
        )


def setup_docker_env(battle_id: str, docker_image_name: str) -> str:
    """
    Pull the docker image and start a container with cybergym_task_dir mounted.
    """
    logging.info(f"Setting up docker env for battle {battle_id}...")
    try:
        client = get_docker_client()
        container_name = f"tooltest_{battle_id}"
        try:
            existing_container = client.containers.get(container_name)
            message = f"Container {container_name} already exists (status: {existing_container.status})."
            logging.info(message)
            return message
        except docker.errors.NotFound:
            pass
        logging.info(f"Pulling image {docker_image_name}...")
        client.images.pull(docker_image_name)
        container = client.containers.run(
            docker_image_name,
            "sleep infinity",
            name=container_name,
            detach=True,
            volumes={
                str(CYBERGYM_TASK_DIR): {
                    "bind": "/cybergym_task_dir",
                    "mode": "rw",
                }
            },
        )
        DOCKER_BATTLE_CONTAINERS[battle_id] = {
            "container_name": container_name
        }
        message = f"Container {container_name} started."
        logging.info(message)
        return message
    except Exception as e:
        error_msg = f"Error setting up docker env: {e}"
        logging.error(error_msg)
        return error_msg


def run_command_in_docker(battle_id: str, command: str) -> str:
    """
    Run a shell command in the specified docker container.
    """
    try:
        client = get_docker_client()
        container_name = f"tooltest_{battle_id}"
        container = client.containers.get(container_name)
        exec_log = container.exec_run(["sh", "-c", command])
        output = exec_log.output.decode()
        logging.info(f"Command: {command}\nOutput: {output}")
        return output
    except docker.errors.NotFound:
        message = f"No container found for battle_id {battle_id}."
        logging.warning(message)
        return message
    except Exception as e:
        error_msg = f"Error running command: {e}"
        logging.error(error_msg)
        return error_msg


def test_cybergym_tools():
    # 1. Start Cybergym server
    result = start_cybergym_server(port=8666)
    logging.info(f"start_cybergym_server result: {result}")
    # 2. Generate Cybergym task
    result = generate_cybergym_task(task_id="arvo:368")
    logging.info(f"generate_cybergym_task result: {result}")
    # 3. Pull a docker image and mount cybergym_task_dir
    battle_id = "test"
    docker_image = DOCKER_IMAGES[0]  # e.g., "cybergym/oss-fuzz-base-runner"
    result = setup_docker_env(battle_id, docker_image)
    logging.info(f"setup_docker_env result: {result}")
    # 4. Run 'ls /cybergym_task_dir' in docker
    result = run_command_in_docker(battle_id, "ls /cybergym_task_dir")
    logging.info(f"ls /cybergym_task_dir result: {result}")
    # 5. Run 'echo -en "\\x00\\x01\\x02\\x03" > $OUT_DIR/poc' in docker
    poc_path = "/cybergym_task_dir/poc"
    result = run_command_in_docker(
        battle_id, f'echo -en "\\x00\\x01\\x02\\x03" > {poc_path}'
    )
    logging.info(f"echo poc result: {result}")
    # 6. Run 'bash $OUT_DIR/submit.sh $OUT_DIR/poc' in docker
    submit_sh = "/cybergym_task_dir/submit.sh"
    result = run_command_in_docker(battle_id, f"bash {submit_sh} {poc_path}")
    logging.info(f"submit.sh result: {result}")


# Example usage:
if __name__ == "__main__":
    # cmd = "pwd"
    # cmd = "source venv/bin/activate && python -m cybergym.server"
    # logging.info(f"Running command: {cmd}")
    # try:
    #     result = subprocess.run(
    #         cmd, capture_output=True, text=True, shell=True
    #     )
    #     logging.info("=== Command Output ===")
    #     logging.info(f"STDOUT:\n{result.stdout.strip()}")
    #     logging.info(f"STDERR:\n{result.stderr.strip()}")
    #     logging.info(f"Return code: {result.returncode}")
    #     logging.info("=====================")
    # except Exception as e:
    #     logging.error(f"Error running command: {e}")
    test_cybergym_tools()
