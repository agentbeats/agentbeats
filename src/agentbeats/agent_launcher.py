# -*- coding: utf-8 -*-

from __future__ import annotations

import time
import asyncio
import uvicorn
import requests
import subprocess
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from agentbeats.utils.agents import get_agent_card

__all__ = ["BeatsAgentLauncher"]


class _SignalPayload(BaseModel):
    backend_url: str
    signal: str
    agent_id: str
    extra_args: Optional[dict] = None


class BeatsAgentLauncher:
    """
    Agent Launcher for AgentBeats.
    Use a separate server to manage agent processes.
    When reset signal is received, it will restart the agent process 
    and notify the backend when the agent is ready.
    E.g. 
        Launcher serves on http://localhost:8000
        Agent runs on http://localhost:8001
        Post to http://localhost:8000/reset with JSON
        {"signal": "reset", "agent_id": "agent123", "extra_args":
            {"arg1": "value1"}} will restart the agent.
        The server will respond to backend_url/agents/{agent_id} with
        {"ready": true} when the agent is ready.
    """

    AGENT_KILL_TIMEOUT = 5

    def __init__(
        self,
        agent_card: str,
        launcher_host: str,
        launcher_port: int,
        agent_host: str,
        agent_port: int,
        model_type: str,
        model_name: str,
        mcp_list: List[str],
        tool_list: List[str]
    ) -> None:
        # agent settings
        self.agent_card = Path(agent_card).expanduser().resolve()
        self.mcp_list = mcp_list
        self.tool_file = tool_list

        # launcher server settings
        self.launcher_host = launcher_host
        self.launcher_port = launcher_port

        # agent server settings
        self.agent_host = agent_host
        self.agent_port = agent_port

        # agent model settings
        self.model_type = model_type
        self.model_name = model_name

        # runtime
        self._app: Optional[FastAPI] = None
        self._agent_proc: Optional[subprocess.Popen] = None
        self._state_lock = asyncio.Lock()

    def _agent_cmd(self) -> List[str]:
        """
        Construct the command to run the agent.
        agentbeats run_agent <card> --tool <tool_file> --mcp <url_list>...
        """
        cmd: List[str] = [
            "agentbeats",
            "run_agent",
            str(self.agent_card),
            "--agent_host", self.agent_host,
            "--agent_port", str(self.agent_port),
            "--model_type", self.model_type,
            "--model_name", self.model_name,
        ]

        for url in self.mcp_list:
            cmd.extend(["--mcp", url])
        
        for tool in self.tool_file:
            cmd.extend(["--tool", tool])

        return cmd

    def _start_agent(self) -> subprocess.Popen:
        print("[Launcher] Starting agent with command:", " ".join(self._agent_cmd()))
        return subprocess.Popen(self._agent_cmd())

    def _terminate_agent(self) -> None:
        if self._agent_proc and self._agent_proc.poll() is None:
            self._agent_proc.terminate()
            try:
                self._agent_proc.wait(timeout=self.AGENT_KILL_TIMEOUT)
            except subprocess.TimeoutExpired:
                self._agent_proc.kill()
                self._agent_proc.wait()

    async def _wait_for_agent_and_notify(self, backend_url: str, agent_id: str) -> None:
        """Background task to wait for agent to be ready and notify backend."""
        max_attempts = 30  # Maximum 60 seconds (30 * 2s)
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(2)  # Wait 2 seconds between checks
            attempt += 1

            agent_card = await get_agent_card(f"http://{self.agent_host}:{self.agent_port}")
            if agent_card:
                try:
                    requests.put(
                        f"{backend_url}/agents/{agent_id}",
                        json={"ready": True},
                        timeout=5,
                    )
                    print(f"[Launcher] Successfully notified backend that agent {agent_id} is ready")
                    return
                except requests.RequestException as e:
                    print(f"[Launcher] WARNING: failed to notify backend: {e}")
                    return
        
        print(f"[Launcher] WARNING: Agent {agent_id} did not become ready within timeout")

    # reset router
    async def _reset_endpoint(self, payload: _SignalPayload) -> dict:
        if payload.signal != "reset":
            raise HTTPException(400, "unsupported signal")

        async with self._state_lock:
            self._terminate_agent()
            self._agent_proc = self._start_agent()
            
            # Start background task to check agent readiness and notify backend
            asyncio.create_task(
                self._wait_for_agent_and_notify(payload.backend_url, payload.agent_id)
            )

            return {"status": "restarting", "pid": self._agent_proc.pid}

    
    def _build_app(self) -> FastAPI:
        app = FastAPI(title="Agent Launcher", version="1.0.0")

        @app.post("/reset")
        async def _reset(payload: _SignalPayload):
            return await self._reset_endpoint(payload=payload)

        @app.get("/status")
        async def _status():
            if self._agent_proc and self._agent_proc.poll() is None:
                return {"status":   "server up, with agent running", 
                        "pid":      self._agent_proc.pid}
            else:
                return {"status": "server up, no agents running"}

        return app

    def run(self, *, reload: bool = False) -> None:
        """
        blocking method to run the launcher server.
        """
        self._agent_proc = self._start_agent()
        self._app = self._build_app()
        uvicorn.run(
            self._app,
            host=self.launcher_host,
            port=self.launcher_port,
            reload=reload,
            log_level="debug" if reload else "info",
        )

    def shutdown(self) -> None:
        self._terminate_agent()
