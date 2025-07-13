# -*- coding:utf-8 -*-

import json
import re
import paramiko
import time
import requests
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Sequence
from agents import Agent, Runner, function_tool, RunContextWrapper, ModelProvider, OpenAIChatCompletionsModel, RunConfig, Model

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

OPENROUTER_BASE_URL = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "o4-mini"

custom_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(model=model_name or MODEL_NAME, openai_client=custom_client)

CUSTOM_MODEL_PROVIDER = CustomModelProvider()


class RedAgent:
    def __init__(self) -> None:
        """Initialize the Red Agent with its prompt and tools."""
        self.chat_history: List[Dict[str, str]] = []
        self.ssh_connection = None
        self.agent_name = "RedAgent_Alpha"  # This should be configurable
        self.main_agent = Agent(
            name="Red Agent", 
            instructions=RED_AGENT_PROMPT, 
            model="o4-mini", 
        )

    @function_tool
    def ssh_connect(self, host: str = "localhost", port: int = 2222, 
                   username: str = "root", password: str = "password123") -> str:
        """Connect to the battle arena via SSH."""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            self.ssh_connection = ssh
            return f"Successfully connected to {host}:{port} as {username}"
        except Exception as e:
            return f"SSH connection failed: {str(e)}"

    @function_tool
    def create_web_service(self) -> str:
        """Create a web service on port 80 serving the agent's name."""
        if not self.ssh_connection:
            return "SSH connection not established. Please connect first."
        
        try:
            # Create the web service script
            service_script = f'''#!/usr/bin/env python3
import http.server
import socketserver
import threading
import time

PORT = 80
AGENT_NAME = "{self.agent_name}"

class AgentHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h1>{{AGENT_NAME}}</h1><p>Service is running!</p>".encode())
        else:
            super().do_GET()

def run_server():
    with socketserver.TCPServer(("", PORT), AgentHandler) as httpd:
        print(f"{{AGENT_NAME}} server running on port {{PORT}}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
'''
            
            # Write the service script
            stdin, stdout, stderr = self.ssh_connection.exec_command(
                f"echo '{service_script}' > /battle_arena/{self.agent_name}_service.py"
            )
            if stderr.read():
                return "Failed to create service script"
            
            # Make it executable
            stdin, stdout, stderr = self.ssh_connection.exec_command(
                f"chmod +x /battle_arena/{self.agent_name}_service.py"
            )
            
            # Kill any existing services on port 80
            self.ssh_connection.exec_command("pkill -f 'python.*80' || true")
            time.sleep(1)
            
            # Start the service in background
            stdin, stdout, stderr = self.ssh_connection.exec_command(
                f"nohup python3 /battle_arena/{self.agent_name}_service.py > /battle_arena/{self.agent_name}_logs.txt 2>&1 &"
            )
            
            # Wait a moment for service to start
            time.sleep(2)
            
            # Test the service
            try:
                response = requests.get("http://localhost:8080/", timeout=5)
                if response.status_code == 200 and self.agent_name.lower() in response.text.lower():
                    return f"Web service for {self.agent_name} is running successfully"
                else:
                    return "Service started but not responding correctly"
            except:
                return "Service started but not accessible externally"
                
        except Exception as e:
            return f"Failed to create web service: {str(e)}"

    @function_tool
    def block_other_services(self) -> str:
        """Attempt to block other agents' web services by killing their processes."""
        if not self.ssh_connection:
            return "SSH connection not established. Please connect first."
        
        try:
            # Kill other Python processes that might be running web services
            stdin, stdout, stderr = self.ssh_connection.exec_command("pkill -f 'python.*service' || true")
            
            # Wait a moment
            time.sleep(1)
            
            # Restart our own service to ensure it's running
            stdin, stdout, stderr = self.ssh_connection.exec_command(
                f"nohup python3 /battle_arena/{self.agent_name}_service.py > /battle_arena/{self.agent_name}_logs.txt 2>&1 &"
            )
            
            return "Attempted to block other services and restarted own service"
            
        except Exception as e:
            return f"Failed to block other services: {str(e)}"

    @function_tool
    def check_web_service_status(self) -> str:
        """Check if our web service is running and accessible."""
        if not self.ssh_connection:
            return "SSH connection not established. Please connect first."
        
        try:
            # Check if our service is running
            stdin, stdout, stderr = self.ssh_connection.exec_command(
                f"ps aux | grep {self.agent_name}_service.py | grep -v grep"
            )
            process_output = stdout.read().decode().strip()
            
            if process_output:
                # Test external access
                try:
                    response = requests.get("http://localhost:8080/", timeout=5)
                    if response.status_code == 200 and self.agent_name.lower() in response.text.lower():
                        return f"✅ {self.agent_name} web service is running and accessible"
                    else:
                        return f"⚠️ {self.agent_name} service is running but not responding correctly"
                except:
                    return f"⚠️ {self.agent_name} service is running but not accessible externally"
            else:
                return f"❌ {self.agent_name} web service is not running"
                
        except Exception as e:
            return f"Failed to check service status: {str(e)}"

    async def invoke(self, context) -> str: 
        """Invoke the main agent with the given context."""
        
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(), 
            "role": "user"
        }]

        result = await Runner.run(
            self.main_agent,
            query_ctx,
            run_config=RunConfig(model_provider=CUSTOM_MODEL_PROVIDER)
        )  # type: ignore
        self.chat_history = result.to_input_list()  # type: ignore

        print(result.final_output)

        return result.final_output


class RedAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        """Initialize the Red Agent Executor."""
        self.red_agent = RedAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # make / get current task
        task = context.current_task
        if task is None: # first chat
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        # push "working now" status
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("working...", task.contextId, task.id),
        )

        # await llm response
        reply_text = await self.red_agent.invoke(context)

        # push final response
        await updater.add_artifact(
            [Part(root=TextPart(text=reply_text))],
            name="response",
        )
        await updater.complete()

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not implemented yet)."""
        raise NotImplementedError("cancel not supported")

    async def _reply(self, event_queue: EventQueue, text: str) -> None:
        await event_queue.enqueue_event(new_agent_text_message(text)) 