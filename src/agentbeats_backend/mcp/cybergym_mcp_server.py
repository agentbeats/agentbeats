# -*- coding: utf-8 -*-

import logging
from fastmcp import FastMCP
import docker
import os
from pathlib import Path
from datetime import datetime
import json
from datasets import load_dataset


# Docker connection settings
DOCKER_SOCKET_PATHS = [
    str(
        Path.home() / ".docker/run/docker.sock"
    ),  # macOS Docker Desktop path (confirmed working)
    "/var/run/docker.sock",  # Standard Linux path
    str(Path.home() / ".docker/desktop/docker.sock"),  # Alternative macOS path
]

# Configure logging once
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Remove any existing handlers to avoid duplicates
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Prevent propagation to root logger to avoid duplicates
logger.propagate = False

# Add single console handler
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("[%(levelname)s] [%(asctime)s] %(message)s")
)
logger.addHandler(handler)


server = FastMCP(
    "Open MCP for AgentBeats Battle Arena",
    host="0.0.0.0",
    port=9001,
)

BACKEND_URL = "http://localhost:9000"

DEBUG_MODE = True


########################################################
# Docker tools
########################################################


def get_docker_client():
    """Get a Docker client using available connection methods."""
    # Try Unix socket connections first
    for socket_path in DOCKER_SOCKET_PATHS:
        if os.path.exists(socket_path):
            try:
                return docker.DockerClient(base_url=f"unix://{socket_path}")
            except Exception:
                continue

    # Fallback to TCP
    try:
        return docker.from_env()
    except Exception as e:
        raise Exception(
            f"Could not connect to Docker daemon. Is Docker running? Error: {e}"
        )


# --- Logging Helpers ---
def append_json_log(log_file: Path, key: str, entry: dict):
    """Append an entry to a JSON log file under the given key."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    if log_file.exists():
        with open(log_file, "r") as f:
            try:
                logs = json.load(f)
            except Exception:
                logs = {key: []}
    else:
        logs = {key: []}
    logs.setdefault(key, []).append(entry)
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)


@server.tool()
def run_terminal_command_in_docker(
    battle_id: str,
    command: str,
    agent_name: str,
) -> str:
    """
    Run a terminal command in the specified docker container for the given battle_id.
    This is for any Red, Blue, or Green agent.
    Logs the command input and output to battle_cmd_history_{battle_id}.json.
    Also, use another MCP server's tool "update_battle_process" to log the command input and the summary of the output.
    """
    try:
        client = get_docker_client()
        container_name = f"cybergym_{battle_id}"
        try:
            container = client.containers.get(container_name)
            exec_log = container.exec_run(["sh", "-c", command])
            message = exec_log.output.decode()
            logger.info("\033[32m" + f"Input Command: {command}" + "\033[0m")
            if len(message) > 200:
                logger.info(
                    "\033[32m"
                    + f"Command output: \n\n {message[:100] + '...' + message[-100:]}"
                    + "\033[0m"
                )
            else:
                logger.info(
                    "\033[32m" + f"Command output: \n\n {message}" + "\033[0m"
                )

            # Log command history
            cmd_log_entry = {
                "timestamp": datetime.now().isoformat(),
                "battle_id": battle_id,
                "agent_name": agent_name,
                "command": command,
                "output": message,
            }
            cmd_log_file = (
                Path("scenarios/cybergym/logs")
                / f"battle_cmd_history_{battle_id}.json"
            )
            append_json_log(cmd_log_file, "cmd_logs", cmd_log_entry)
            logger.info(f"Command history recorded to {cmd_log_file}")

            return message
        except docker.errors.NotFound:
            message = f"No container found for battle_id {battle_id}."
            logger.warning(message)
            return message
    except Exception as e:
        error_msg = f"Error running command: {e}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    import argparse

    # parse args
    parser = argparse.ArgumentParser(
        description="Run the Sec-Bench MCP server with a configurable port.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9002,
        help="TCP port for the HTTP server to listen on (default: 9002)",
    )
    args = parser.parse_args()

    server.run(
        transport="sse",
        host="0.0.0.0",
        port=args.port,
        log_level="ERROR",
    )
