#!/usr/bin/env python3

import subprocess
import requests
import logging
import time
import os
import sys
import signal
import threading
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# Configuration
TASK_IDS = [
    "arvo:368",
    "arvo:1065",
    "arvo:3938",
    "arvo:10400",
    "arvo:24993",
    "oss-fuzz:42535201",
    "oss-fuzz:42535468",
    "oss-fuzz:370689421",
    "oss-fuzz:385167047",
]
START_PORT = 8333
BACKEND_URL = "http://localhost:9000/agents"
PROJECT_DIR = os.getcwd()  # Use current working directory
AGENT_CARD_TEMPLATE_PATH = "scenarios/cybergym/green_agent/agent_card.toml.j2"

# Process management
processes: List[subprocess.Popen] = []
backend_process: Optional[subprocess.Popen] = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def cleanup_processes():
    """Clean up all spawned processes."""
    global processes, backend_process

    logging.info("Cleaning up processes...")

    # Kill all agent processes
    for proc in processes:
        if proc.poll() is None:  # Process is still running
            logging.info(f"Terminating process {proc.pid}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logging.warning(f"Force killing process {proc.pid}")
                proc.kill()

    # Kill backend process
    if backend_process and backend_process.poll() is None:
        logging.info(f"Terminating backend process {backend_process.pid}")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logging.warning(
                f"Force killing backend process {backend_process.pid}"
            )
            backend_process.kill()


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    logging.info("Received interrupt signal, cleaning up...")
    cleanup_processes()
    sys.exit(0)


def run_command(
    command: List[str], cwd: str = None, env: Dict[str, str] = None
) -> subprocess.Popen:
    """Run a command and return the process."""
    logging.info(f"Running command: {' '.join(command)}")
    if cwd:
        logging.info(f"Working directory: {cwd}")

    return subprocess.Popen(
        command,
        cwd=cwd or PROJECT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def generate_agent_card(task_id: str, agent_port: int) -> bool:
    """Generate an agent card for the given ARVO ID."""
    logging.info(
        f"Generating agent card for task ID: {task_id} on port {agent_port}"
    )

    cmd = [
        "python",
        "scenarios/cybergym/green_agent/generate_agent_card.py",
        "--agent-name",
        f"[CyberGym] {task_id}",
        "--task-id",
        task_id,
        "--template",
        AGENT_CARD_TEMPLATE_PATH,
        "--output",
        f"scenarios/cybergym/green_agent/agent_card_{task_id}.toml",
        "--host",
        "0.0.0.0",
        "--port",
        str(agent_port),
    ]

    try:
        result = subprocess.run(
            cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            logging.info(f"✓ Successfully generated agent_card_{task_id}.toml")
            return True
        else:
            logging.error(
                f"✗ Failed to generate agent card for task ID {task_id}: {result.stderr}"
            )
            return False
    except subprocess.TimeoutExpired:
        logging.error(f"✗ Timeout generating agent card for task ID {task_id}")
        return False
    except Exception as e:
        logging.error(
            f"✗ Exception generating agent card for task ID {task_id}: {e}"
        )
        return False


def start_backend() -> subprocess.Popen:
    """Start the backend server."""
    logging.info("Starting backend server...")

    # Set up environment with virtual environment
    env = os.environ.copy()
    venv_path = os.path.join(PROJECT_DIR, "venv", "bin", "python")

    if os.path.exists(venv_path):
        logging.info(f"Using virtual environment: {venv_path}")
        cmd = [venv_path, "-m", "src.backend.run"]
    else:
        cmd = ["python", "-m", "src.backend.run"]

    return run_command(cmd, cwd=PROJECT_DIR, env=env)


def start_agent(
    task_id: str, launcher_port: int, agent_port: int
) -> subprocess.Popen:
    """Start an agent for the given ARVO ID."""
    logging.info(
        f"Starting agent for task ID: {task_id} (launcher_port: {launcher_port}, agent_port: {agent_port})"
    )

    # Set up environment with virtual environment
    env = os.environ.copy()
    venv_path = os.path.join(PROJECT_DIR, "venv", "bin")
    if os.path.exists(venv_path):
        agentbeats_cmd = os.path.join(venv_path, "agentbeats")
        if not os.path.exists(agentbeats_cmd):
            agentbeats_cmd = "agentbeats"
    else:
        agentbeats_cmd = "agentbeats"

    cmd = [
        agentbeats_cmd,
        "run",
        f"green_agent/agent_card_{task_id}.toml",
        "--launcher_port",
        str(launcher_port),
        "--agent_port",
        str(agent_port),
        "--backend",
        "http://localhost:9000",
        "--mcp",
        "http://localhost:9001/sse",
        "--mcp",
        "http://localhost:9002/sse",
        "--tool",
        "green_agent/tools.py",
    ]

    return run_command(
        cmd, cwd=os.path.join(PROJECT_DIR, "scenarios", "cybergym"), env=env
    )


def wait_for_backend(timeout: int = 30) -> bool:
    """Wait for the backend to be ready."""
    logging.info("Waiting for backend to be ready...")

    for i in range(timeout):
        try:
            response = requests.get("http://localhost:9000/health", timeout=1)
            if response.status_code == 200:
                logging.info("✓ Backend is ready")
                return True
        except requests.RequestException:
            pass

        time.sleep(1)

    logging.error("✗ Backend failed to start within timeout")
    return False


def wait_for_agent(port: int, timeout: int = 30) -> bool:
    """Wait for an agent to be ready."""
    logging.info(f"Waiting for agent on port {port} to be ready...")

    for i in range(timeout):
        try:
            response = requests.get(
                f"http://localhost:{port}/.well-known/agent.json", timeout=1
            )
            if response.status_code == 200:
                logging.info(f"✓ Agent on port {port} is ready")
                return True
        except requests.RequestException:
            pass

        time.sleep(1)

    logging.error(f"✗ Agent on port {port} failed to start within timeout")
    return False


def register_agent(task_id: str, launcher_port: int, agent_port: int) -> bool:
    """Register an agent with the backend."""
    agent_url = f"http://0.0.0.0:{agent_port}"
    launcher_url = f"http://0.0.0.0:{launcher_port}"
    alias = f"[CyberGym] {task_id}"
    name = alias

    payload = {
        "alias": alias,
        "agent_url": agent_url,
        "launcher_url": launcher_url,
        "is_green": True,
        "participant_requirements": [
            {"role": "red_agent", "name": "poc_generator", "required": True}
        ],
        "battle_timeout": 1200,
        "roles": {},
        "name": name,
    }

    try:
        logging.info(f"Registering agent for task ID: {task_id}")
        response = requests.post(BACKEND_URL, json=payload, timeout=10)
        if response.status_code == 201:
            logging.info(f"✓ [{name}] Registered successfully")
            return True
        else:
            logging.error(
                f"✗ [{name}] Registration failed: {response.status_code} {response.text}"
            )
            return False
    except Exception as e:
        logging.error(f"✗ [{name}] Exception during registration: {e}")
        return False


def stream_output(process: subprocess.Popen, name: str):
    """Stream process output to logs."""

    def log_stdout():
        for line in iter(process.stdout.readline, ""):
            if line.strip():
                logging.info(f"[{name}] {line.strip()}")

    def log_stderr():
        for line in iter(process.stderr.readline, ""):
            if line.strip():
                logging.warning(f"[{name}] {line.strip()}")

    stdout_thread = threading.Thread(target=log_stdout, daemon=True)
    stderr_thread = threading.Thread(target=log_stderr, daemon=True)

    stdout_thread.start()
    stderr_thread.start()


def main():
    global processes, backend_process

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate and register/run CyberGym agents"
    )
    parser.add_argument(
        "--skip-register",
        action="store_true",
        help="Skip agent registration step and only run already-registered agents",
    )
    args = parser.parse_args()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.skip_register:
        logging.info(
            "Starting batch agent execution (skipping registration)..."
        )
    else:
        logging.info("Starting batch agent generation and registration...")

    # Change to project directory
    os.chdir(PROJECT_DIR)

    try:
        # Step 1: Generate agent cards
        logging.info("=== STEP 1: Generating Agent Cards ===")
        successful_generations = []
        current_port = START_PORT
        for task_id in TASK_IDS:
            agent_port = current_port + 1  # agent_port is launcher_port + 1
            if generate_agent_card(task_id, agent_port):
                successful_generations.append(task_id)
            current_port += 2

        if not successful_generations:
            logging.error("No agent cards generated successfully. Exiting.")
            return 1

        logging.info(
            f"Successfully generated {len(successful_generations)} agent cards"
        )

        # Step 2: Start backend
        logging.info("=== STEP 2: Starting Backend ===")
        backend_process = start_backend()
        stream_output(backend_process, "BACKEND")

        if not wait_for_backend():
            logging.error("Backend failed to start. Exiting.")
            return 1

        # Step 3: Start agents
        logging.info("=== STEP 3: Starting Agents ===")
        current_port = START_PORT
        agent_info = []

        for task_id in successful_generations:
            launcher_port = current_port
            agent_port = current_port + 1

            agent_process = start_agent(task_id, launcher_port, agent_port)
            processes.append(agent_process)
            stream_output(agent_process, f"AGENT-{task_id}")

            agent_info.append(
                {
                    "task_id": task_id,
                    "launcher_port": launcher_port,
                    "agent_port": agent_port,
                }
            )

            current_port += 2

        # Step 4: Wait for agents to be ready
        logging.info("=== STEP 4: Waiting for Agents ===")
        time.sleep(5)  # Give agents time to start

        ready_agents = []
        for info in agent_info:
            if wait_for_agent(info["agent_port"]):
                ready_agents.append(info)

        # Step 5: Register agents (conditional)
        if args.skip_register:
            logging.info("=== STEP 5: Skipping Agent Registration ===")
            logging.info("Agents are assumed to be already registered")
            successful_registrations = len(ready_agents)
        else:
            logging.info("=== STEP 5: Registering Agents ===")
            time.sleep(2)  # Additional wait before registration

            successful_registrations = 0
            for info in ready_agents:
                if register_agent(
                    info["task_id"], info["launcher_port"], info["agent_port"]
                ):
                    successful_registrations += 1
                time.sleep(1)  # Delay between registrations

            logging.info(
                f"Successfully registered {successful_registrations}/{len(ready_agents)} agents"
            )

        # Step 6: Keep running
        logging.info("=== All agents started and registered! ===")
        logging.info("Press Ctrl+C to stop all processes")

        # Keep the script running
        try:
            while True:
                # Check if any critical processes have died
                if backend_process.poll() is not None:
                    logging.error("Backend process has died!")
                    break

                time.sleep(5)
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1

    finally:
        cleanup_processes()

    return 0


if __name__ == "__main__":
    sys.exit(main())
