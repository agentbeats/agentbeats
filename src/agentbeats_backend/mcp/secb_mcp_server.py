# -*- coding: utf-8 -*-

"""
This MCP is used to setup the Docker environment for the Sec-Bench CVE instance.

Todo:
- [ ] Support for tracking a docker container env for each CVE instance / battle ID
- [ ] How to hide some orchestration tools from BLUE & RED agents?

For demo, the docker path will be:
hwiwonlee/secb.eval.x86_64.gpac.cve-2023-5586:poc
"""

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


HUGGINGFACE_DATASET_NAME = "SEC-bench/SEC-bench"

# Configure logging once
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
logger = logging.getLogger(__name__)

# Remove console handler to avoid duplicates
logger.handlers = []
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
        container_name = f"secb_battle_{battle_id}"
        try:
            if DEBUG_MODE and command == "secb build":
                message = "BUILD SUCCESS"
            elif DEBUG_MODE and command == "secb repro":
                message = "PoC Successfully Triggered"
            else:
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
                Path("scenarios/sec_bench/logs")
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


########################################################
# Battle progress tracking
########################################################


# @server.tool()
# def update_battle_process(
#     battle_id: str,
#     message: str,
#     reported_by: str,
#     detail: dict = None,
# ) -> str:
#     """
#     Log intermediate steps and information during the battle.

#     Parameters:
#     - battle_id: The unique battle session identifier
#     - message: Simple, human-readable description of what happened
#     - reported_by: The agent/role reporting this information ("green_agent", "red_agent", or "blue_agent")
#     - detail: Optional structured data with specific event details
#     """
#     try:
#         timestamp = datetime.now().isoformat()
#         log_entry = {
#             "timestamp": timestamp,
#             "battle_id": battle_id,
#             "message": message,
#             "reported_by": reported_by,
#             "detail": detail or {},
#         }

#         # Log to console
#         logger.info(
#             f"Battle progress update for {battle_id}: {message} (by {reported_by})"
#         )
#         if detail:
#             logger.debug(f"Details: {detail}")

#         # Save to JSON file with per-battle naming
#         log_file = (
#             Path("scenarios/sec_bench/logs") / f"battle_log_{battle_id}.json"
#         )
#         append_json_log(log_file, "battle_logs", log_entry)

#         # log where it was saved to
#         logger.info(f"Battle progress recorded to {log_file}")

#         return f"Battle progress recorded: {message}"
#     except Exception as e:
#         error_msg = f"Error updating battle progress: {e}"
#         logger.error(error_msg)
#         return error_msg


# @server.tool()
# def report_on_battle_end(
#     battle_id: str,
#     winner: str,
#     score: dict,
#     detail: dict = None,
# ) -> str:
#     """
#     Report the final battle result.

#     Parameters:
#     - battle_id: The unique battle session identifier
#     - winner: Either "red_agent" or "blue_agent"
#     - score: Dictionary containing scoring details
#     - detail: Optional additional information about the battle outcome
#     """
#     try:
#         timestamp = datetime.now().isoformat()
#         log_entry = {
#             "timestamp": timestamp,
#             "battle_id": battle_id,
#             "type": "battle_end",
#             "winner": winner,
#             "score": score,
#             "detail": detail or {},
#         }

#         # Log to console
#         logger.info(f"Battle {battle_id} ended. Winner: {winner}")
#         logger.info(f"Score: {score}")
#         if detail:
#             logger.debug(f"Details: {detail}")

#         # Save to JSON file with per-battle naming
#         log_file = (
#             Path("scenarios/sec_bench/logs") / f"battle_log_{battle_id}.json"
#         )
#         append_json_log(log_file, "battle_logs", log_entry)

#         return f"Battle end recorded. Winner: {winner}"
#     except Exception as e:
#         error_msg = f"Error reporting battle end: {e}"
#         logger.error(error_msg)
#         return error_msg


########################################################
# Sec-Bench Huggingface Dataset tools
########################################################


@server.tool()
def get_instance_details(instance_id: str) -> dict:
    """
    Get details for a given instance ID from the SEC-bench dataset, including:
    - workspace directory name
    - sanitizer report
    - bug report

    Parameters:
    - instance_id: The unique identifier for the instance in the dataset

    Returns:
    - dict with keys: 'work_dir', 'sanitizer_report', 'bug_report', or an error message if not found.
    """
    try:
        # Load the SEC-bench dataset
        dataset = load_dataset(HUGGINGFACE_DATASET_NAME, split="eval")

        logger.info(
            f"[get_instance_details] Loaded dataset for instance ID: {instance_id}"
        )

        # Find the instance with matching ID
        for instance in dataset:
            if instance["instance_id"] == instance_id:
                logger.info(
                    f"[get_instance_details] Found details for instance: {instance_id}"
                )
                return {
                    "work_dir": instance.get("work_dir", None),
                    "sanitizer_report": instance.get("sanitizer_report", None),
                    "bug_report": instance.get("bug_report", None),
                }

        return {"error": f"No instance found with ID {instance_id}"}
    except Exception as e:
        error_msg = f"Error getting instance details: {e}"
        logger.error(error_msg)
        return {"error": error_msg}


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
