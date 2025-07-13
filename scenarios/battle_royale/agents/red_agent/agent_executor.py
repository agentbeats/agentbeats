# -*- coding:utf-8 -*-

import httpx
import json
import re
import subprocess
import time
import asyncio
import paramiko
import requests
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Sequence
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerSse
from uuid import uuid4
import sys
import os
from pathlib import Path

from prompt import RED_AGENT_PROMPT

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart
from a2a.utils import new_task, new_agent_text_message

import os
from openai import AsyncOpenAI
from agents import ModelProvider, OpenAIChatCompletionsModel, RunConfig
from agents import set_tracing_disabled
set_tracing_disabled(disabled=True)
from agents import Model

OPENROUTER_BASE_URL = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "o4-mini"

custom_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(model=model_name or MODEL_NAME, openai_client=custom_client)

CUSTOM_MODEL_PROVIDER = CustomModelProvider()

class RedAgent:
    def __init__(self, mcp_url: str | None = None) -> None:
        """Initialize the Red Agent with its prompt and tools."""
        import os
        print("[RedAgent] ENV OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
        print("[RedAgent] ENV OPENAI_API_BASE:", os.getenv("OPENAI_API_BASE"))
        print("[RedAgent] Model for main_agent:", "o4-mini")
        self._httpx_client: httpx.AsyncClient = httpx.AsyncClient()

        # URL for the MCP server (optional)
        self.mcp_url = mcp_url
        self.mcp_servers = []
        if self.mcp_url:
            self.mcp_servers.append(MCPServerSse(
                name="Battle Royale MCP Server",
                params={
                    "url": self.mcp_url, 
                }, 
                cache_tools_list=True,
            ))
        self.mcp_servers_connected = False

        # Battle state
        self.agent_id = None
        self.ssh_connected = False
        self.web_service_running = False
        self.service_id = None
        self.ssh_client = None

        # Initialize chat history and tools
        self.chat_history: List[Dict[str, str]] = []
        self.tool_list: Sequence = [
            self._create_ssh_connection_tool(),
            self._create_ssh_command_tool(),
            self._create_web_service_tool(),
            self._create_service_blocking_tool(),
            self._create_service_status_tool(),
            self._create_reset_tool(),
            self._create_set_identifier_tool(),
        ]

    async def ensure_mcp_connected(self) -> None:
        """Ensure the MCP server is connected."""
        if not self.mcp_servers_connected and self.mcp_servers:
            for server in self.mcp_servers:
                await server.connect()
            
            self.main_agent = Agent(
                name="Red Agent", 
                instructions=RED_AGENT_PROMPT, 
                model="o4-mini", 
                tools=self.tool_list,
                mcp_servers=self.mcp_servers, 
            )

            self.mcp_servers_connected = True
        elif not self.mcp_servers:
            # No MCP server, create agent without it
            self.main_agent = Agent(
                name="Red Agent", 
                instructions=RED_AGENT_PROMPT, 
                model="o4-mini", 
                tools=self.tool_list,
            )

    def _create_ssh_connection_tool(self):
        @function_tool(name_override="connect_to_battle_arena")
        def connect_to_battle_arena(host: str = "localhost", port: int = 2222, username: str = "battle", password: str = "battle123") -> str:
            """
            Connect to the battle arena via SSH.
            This establishes a connection to the Docker container where the battle takes place.
            """
            try:
                # Create SSH client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect to the arena
                self.ssh_client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=10
                )
                
                # Test the connection
                stdin, stdout, stderr = self.ssh_client.exec_command("echo 'SSH connection successful' && pwd")
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                if error:
                    return f"❌ SSH connection error: {error}"
                
                self.ssh_connected = True
                return f"✅ Successfully connected to battle arena via SSH\nOutput: {output}"
                
            except Exception as e:
                return f"❌ Failed to connect to battle arena: {str(e)}"
        
        return connect_to_battle_arena

    def _create_ssh_command_tool(self):
        @function_tool(name_override="execute_ssh_command")
        def execute_ssh_command(command: str) -> str:
            """
            Execute a command directly in the SSH terminal of the battle arena.
            This is your primary tool for interacting with the remote system.
            
            Examples:
            - "ls -la" - List files in current directory
            - "ps aux | grep python" - Check running Python processes
            - "ss -tuln | grep :80" - Check what's using port 80
            - "python3 -m http.server 80" - Start a simple web server
            - "pkill -f http.server" - Kill web server processes
            - "curl http://localhost:80" - Test web service
            """
            if not self.ssh_connected:
                return "❌ Not connected to battle arena. Use connect_to_battle_arena first."
            
            try:
                # Execute the command via SSH
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                
                # Get output and error
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                # Wait for command to complete
                exit_status = stdout.channel.recv_exit_status()
                
                result = f"Command: {command}\nExit Status: {exit_status}\n"
                
                if output:
                    result += f"Output:\n{output}\n"
                
                if error:
                    result += f"Error:\n{error}\n"
                
                if exit_status == 0:
                    return f"✅ {result}"
                else:
                    return f"⚠️ {result}"
                
            except Exception as e:
                return f"❌ Error executing command '{command}': {str(e)}"
        
        return execute_ssh_command

    def _create_web_service_tool(self):
        @function_tool(name_override="create_web_service")
        def create_web_service(service_name: str = None, port: int = 80) -> str:
            """
            Create a web service on the specified port in the battle arena.
            The service should serve the agent's name and be accessible on port 80.
            """
            if not self.ssh_connected:
                return "❌ Not connected to battle arena. Use connect_to_battle_arena first."
            
            try:
                # Generate service name if not provided
                if not service_name:
                    service_name = f"red_agent_service_{int(time.time())}"
                
                # Create a simple Python web service
                service_code = f'''#!/usr/bin/env python3
import http.server
import socketserver
import time

class BattleService(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            response = f"""
            <html>
            <head><title>Battle Royale Service</title></head>
            <body>
                <h1>🏆 {service_name}</h1>
                <p>This is a web service created by a red agent in the battle royale.</p>
                <p>Time: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Agent ID: {self.agent_id or 'Unknown'}</strong></p>
                <p>Service Status: Active and Running</p>
            </body>
            </html>
            """
            
            # Simple text response for easier monitoring
            text_response = f"RedAgent: Alive and Kicking\nService: Battle Royale on port 80\nAgent ID: {self.agent_id or 'Unknown'}"
            
            response = html_response
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

if __name__ == "__main__":
    PORT = {port}
    with socketserver.TCPServer(("", PORT), BattleService) as httpd:
        print(f"Server running on port {{PORT}}")
        httpd.serve_forever()
'''
                
                # Write service code to remote server
                service_file = f"/tmp/{service_name}.py"
                stdin, stdout, stderr = self.ssh_client.exec_command(f"cat > {service_file}")
                stdin.write(service_code)
                stdin.close()
                
                # Make the service executable
                self.ssh_client.exec_command(f"chmod +x {service_file}")
                
                # Start the service in background
                start_command = f"nohup python3 {service_file} > /tmp/{service_name}.log 2>&1 & echo $!"
                stdin, stdout, stderr = self.ssh_client.exec_command(start_command)
                pid = stdout.read().decode().strip()
                
                if pid and pid.isdigit():
                    self.web_service_running = True
                    self.service_id = service_name
                    return f"✅ Web service '{service_name}' started successfully on port {port} (PID: {pid})"
                else:
                    return f"❌ Failed to start web service. Check logs: /tmp/{service_name}.log"
                
            except Exception as e:
                return f"❌ Error creating web service: {str(e)}"
        
        return create_web_service

    def _create_service_blocking_tool(self):
        @function_tool(name_override="block_other_services")
        def block_other_services() -> str:
            """
            Attempt to block other agents' web services from running.
            This is a competitive action in the battle royale.
            """
            if not self.ssh_connected:
                return "❌ Not connected to battle arena. Use connect_to_battle_arena first."
            
            try:
                # Find processes using port 80
                stdin, stdout, stderr = self.ssh_client.exec_command("ss -tuln | grep :80")
                port_80_processes = stdout.read().decode().strip()
                
                if not port_80_processes:
                    return "ℹ️ No services currently running on port 80"
                
                # Find Python processes that might be web services
                stdin, stdout, stderr = self.ssh_client.exec_command("ps aux | grep python | grep -v grep")
                python_processes = stdout.read().decode().strip()
                
                blocked_count = 0
                if python_processes:
                    for line in python_processes.split('\n'):
                        if line.strip():
                            parts = line.split()
                            if len(parts) > 1:
                                pid = parts[1]
                                # Don't kill our own service
                                if self.service_id and self.service_id not in line:
                                    try:
                                        self.ssh_client.exec_command(f"kill {pid}")
                                        blocked_count += 1
                                    except:
                                        pass
                
                if blocked_count > 0:
                    return f"✅ Blocked {blocked_count} competing web services"
                else:
                    return "ℹ️ No competing services found to block"
                
            except Exception as e:
                return f"❌ Error blocking services: {str(e)}"
        
        return block_other_services

    def _create_service_status_tool(self):
        @function_tool(name_override="check_service_status")
        def check_service_status() -> str:
            """
            Check the status of the current web service and other services in the arena.
            """
            if not self.ssh_connected:
                return "❌ Not connected to battle arena. Use connect_to_battle_arena first."
            
            try:
                status_report = {
                    "ssh_connected": self.ssh_connected,
                    "web_service_running": self.web_service_running,
                    "service_id": self.service_id,
                    "agent_id": self.agent_id
                }
                
                # Check if our service is still running
                if self.service_id:
                    stdin, stdout, stderr = self.ssh_client.exec_command(f"ps aux | grep {self.service_id} | grep -v grep")
                    service_running = stdout.read().decode().strip()
                    status_report["our_service_active"] = bool(service_running)
                
                # Check port 80 usage
                stdin, stdout, stderr = self.ssh_client.exec_command("ss -tuln | grep :80")
                port_80_status = stdout.read().decode().strip()
                status_report["port_80_services"] = len(port_80_status.split('\n')) if port_80_status else 0
                
                # Check service manager
                try:
                    services_response = requests.get("http://localhost:9099/services", timeout=5)
                    if services_response.status_code == 200:
                        services = services_response.json()
                        status_report["registered_services"] = len(services)
                    else:
                        status_report["registered_services"] = 0
                except:
                    status_report["registered_services"] = 0
                
                return f"📊 Service Status Report:\n{json.dumps(status_report, indent=2)}"
                
            except Exception as e:
                return f"❌ Error checking service status: {str(e)}"
        
        return check_service_status

    def _create_reset_tool(self):
        @function_tool(name_override="reset_agent_state")
        def reset_agent_state() -> str:
            """
            Reset the red agent state to initial state.
            This stops any running services and clears the agent's state.
            """
            try:
                # Stop our web service if running
                if self.service_id and self.ssh_connected:
                    self.ssh_client.exec_command(f"pkill -f {self.service_id}")
                
                # Close SSH connection
                if self.ssh_client:
                    self.ssh_client.close()
                
                # Reset state
                self.ssh_connected = False
                self.web_service_running = False
                self.service_id = None
                self.ssh_client = None
                
                return "✅ Agent state reset successfully"
                
            except Exception as e:
                return f"❌ Error resetting agent state: {str(e)}"
        
        return reset_agent_state

    def _create_set_identifier_tool(self):
        @function_tool(name_override="set_agent_identifier")
        def set_agent_identifier(identifier: str) -> str:
            """
            Set the agent's identifier for the battle arena.
            This is used to ensure the web service serves the correct agent.
            """
            self.agent_id = identifier
            return f"✅ Agent identifier set to: {identifier}"
        
        return set_agent_identifier

    async def invoke(self, context) -> str:
        print(context.get_user_input(), "=========================================RED INPUT")
        await self.ensure_mcp_connected()
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(),
            "role": "user"
        }]
        result = await Runner.run(
            self.main_agent,
            query_ctx,
            max_turns=100,
            run_config=RunConfig(model_provider=CUSTOM_MODEL_PROVIDER)
        )  # type: ignore
        self.chat_history = result.to_input_list()  # type: ignore
        print(result.final_output, "=========================================RED OUTPUT")
        return result.final_output

class RedAgentExecutor(AgentExecutor):
    def __init__(self, mcp_url: str | None = None) -> None:
        """Initialize the Red Agent Executor."""
        self.red_agent = RedAgent(mcp_url=mcp_url)

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task = context.current_task
        if task is None: # first chat
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("working...", task.contextId, task.id),
        )
        reply_text = await self.red_agent.invoke(context)
        await updater.add_artifact(
            [Part(root=TextPart(text=reply_text))],
            name="response",
        )
        await updater.complete()

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise NotImplementedError("cancel not supported")

    async def _reply(self, event_queue: EventQueue, text: str) -> None:
        await event_queue.enqueue_event(new_agent_text_message(text)) 