from __future__ import annotations

"""
agent_controller.py – controls an external agent server.

Run this script to launch two HTTP endpoints:
 1. A controller FastAPI service on --port (default 8000).
 2. A child agent process started from a Python file given via --file, served
    on (--port + 1).

POST {controller}/ with JSON {"signal": "reset"} will restart the child agent
and respond with its fresh PID and URL.
"""

import uvicorn
import argparse
import asyncio
import shlex
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Agent Controller", version="0.4.0")

AGENT_FILE: str = ""
BASE_PORT: int = 8000
CHILD_PORT: int = BASE_PORT + 1
agent_proc: Optional[subprocess.Popen] = None
state_lock = asyncio.Lock()
AGENT_KILL_TIMEOUT = 5

class SignalPayload(BaseModel):
    signal: str
    extra_args: Optional[dict] = None


def _agent_cmd(extra_args) -> list[str]:
    global AGENT_FILE

    cmd = [
        "python",
        AGENT_FILE,
    ]

    for name, val in extra_args.items():
        if isinstance(val, bool):
            cmd.append(f"--{name}")
        else:
            cmd.append(f"--{name}={val}")
    
    print(cmd)

    return cmd


def _start_agent(extra_args) -> subprocess.Popen:
    return subprocess.Popen(_agent_cmd(extra_args))


def _terminate_agent(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=AGENT_KILL_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@app.post("/reset")
async def reset(payload: SignalPayload):
    if payload.signal != "reset":
        raise HTTPException(status_code=400, detail="unsupported signal")

    global agent_proc
    async with state_lock:
        if agent_proc and agent_proc.poll() is None:
            _terminate_agent(agent_proc)
        agent_proc = _start_agent(extra_args=payload.extra_args or {})
        return {
            "status": "restarted",
            "pid": agent_proc.pid,
        }


def _parse_cli() -> argparse.Namespace:
    p = argparse.ArgumentParser("Agent Controller")
    p.add_argument("--file", required=True, help="Path to the agent Python file to run")
    p.add_argument("--host", default="0.0.0.0", help="Bind address for controller")
    p.add_argument("--port", type=int, default=8000, help="Controller port")
    p.add_argument("--reload", action="store_true", help="Uvicorn autoreload")
    return p.parse_args()


def main() -> None:
    global AGENT_FILE, BASE_PORT, CHILD_PORT

    args = _parse_cli()
    AGENT_FILE = args.file
    BASE_PORT = args.port
    CHILD_PORT = BASE_PORT + 1

    print(AGENT_FILE, BASE_PORT, CHILD_PORT)

    uvicorn.run(app, host=args.host, port=BASE_PORT, reload=False)


if __name__ == "__main__":
    main()
