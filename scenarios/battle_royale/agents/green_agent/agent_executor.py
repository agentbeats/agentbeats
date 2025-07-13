# -*- coding:utf-8 -*-

import httpx
import json
import re
import subprocess
import time
import asyncio
import logging
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Sequence
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerSse
from uuid import uuid4
import sys
import os
from pathlib import Path

from prompt import GREEN_AGENT_PROMPT

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart
from a2a.utils import new_task, new_agent_text_message

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    Message,
    MessageSendParams,
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    Role,
    Part,
    TextPart,
    AgentCard,
)

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

class GreenAgent:
    def __init__(self, mcp_url: str = None) -> None:
        """Initialize the Green Agent with its prompt and tools."""
        import os
        print("[GreenAgent] ENV OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
        print("[GreenAgent] ENV OPENAI_API_BASE:", os.getenv("OPENAI_API_BASE"))
        print("[GreenAgent] Model for main_agent:", "o4-mini")
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger("battle_royale_green_agent")
        self.logger.info("Green Agent initialized")
        
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
        self.battle_id = None
        self.red_agents = []
        self.battle_start_time = None
        self.battle_duration = 300  # 5 minutes default
        self.monitoring_interval = 60  # 1 minute
        
        # Uptime tracking
        self.uptime_data = {}  # {agent_id: {total_checks: int, successful_checks: int}}
        self.battle_log = []  # List of battle events

        # Initialize chat history and tools
        self.chat_history: List[Dict[str, str]] = []
        self.tool_list: Sequence = [
            self._create_docker_management_tool(),
            self._create_battle_monitoring_tool(),
            self._create_agent_communication_tool(),
            self._create_battle_control_tool(),
            self._create_uptime_tracking_tool(),
            self._create_winner_determination_tool(),
            self._create_battle_summary_tool(),
        ]

    def _setup_logging(self):
        """Setup logging configuration for the battle royale"""
        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(logs_dir / "battle_royale.log"),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        # Create a specific logger for battle royale
        logger = logging.getLogger("battle_royale_green_agent")
        logger.setLevel(logging.INFO)
        
        # Log initial setup
        logger.info("Battle Royale logging system initialized")
        logger.info(f"Log file: {logs_dir / 'battle_royale.log'}")

    async def ensure_mcp_connected(self) -> None:
        """Ensure the MCP server is connected."""
        if not self.mcp_servers_connected and self.mcp_servers:
            for server in self.mcp_servers:
                await server.connect()
            
            self.main_agent = Agent(
                name="Green Agent", 
                instructions=GREEN_AGENT_PROMPT, 
                model="o4-mini", 
                tools=self.tool_list,
                mcp_servers=self.mcp_servers, 
            )

            self.mcp_servers_connected = True
        elif not self.mcp_servers:
            # No MCP server, create agent without it
            self.main_agent = Agent(
                name="Green Agent", 
                instructions=GREEN_AGENT_PROMPT, 
                model="o4-mini", 
                tools=self.tool_list,
            )

    async def _make_client(self, base_url: str) -> A2AClient:
        resolver = A2ACardResolver(
            httpx_client=self._httpx_client,
            base_url=base_url,
        )
        card: AgentCard | None = await resolver.get_agent_card(
            relative_card_path="/.well-known/agent.json"
        )
        if card is None:
            raise RuntimeError(f"Failed to resolve agent card from {base_url}")
        return A2AClient(httpx_client=self._httpx_client, agent_card=card)

    def _create_docker_management_tool(self):
        @function_tool(name_override="create_battle_arena")
        def create_battle_arena(battle_id: str, num_red_agents: int = 2) -> str:
            """
            Create a Docker container for the battle royale arena.
            This sets up the environment where red agents will compete.
            """
            self.logger.info(f"Creating battle arena: battle_id={battle_id}, num_red_agents={num_red_agents}")
            
            try:
                # Change to docker directory
                docker_dir = Path(__file__).parent.parent.parent / "docker"
                os.chdir(docker_dir)
                
                # Stop any existing containers
                self.logger.info("Stopping existing containers")
                subprocess.run(["docker-compose", "down"], capture_output=True)
                
                # Start the battle arena
                self.logger.info("Starting battle arena with docker-compose")
                result = subprocess.run(
                    ["docker-compose", "up", "-d", "--build"], 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    self.battle_id = battle_id
                    self.red_agents = [f"red_agent_{i}" for i in range(num_red_agents)]
                    self.logger.info(f"Battle arena created successfully: {battle_id} with {num_red_agents} agents")
                    return f"✅ Battle arena created successfully for battle {battle_id} with {num_red_agents} red agents"
                else:
                    self.logger.error(f"Failed to create battle arena: {result.stderr}")
                    return f"❌ Failed to create battle arena: {result.stderr}"
                    
            except Exception as e:
                self.logger.error(f"Error creating battle arena: {str(e)}")
                return f"❌ Error creating battle arena: {str(e)}"
        
        return create_battle_arena

    def _create_battle_monitoring_tool(self):
        @function_tool(name_override="monitor_battle_progress")
        def monitor_battle_progress() -> str:
            """
            Monitor the current state of the battle royale.
            Check service status, agent progress, and calculate scores.
            """
            try:
                # Check if battle arena is running
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=battle-royale-arena", "--format", "{{.Names}}"],
                    capture_output=True, 
                    text=True
                )
                
                if "battle-royale-arena" not in result.stdout:
                    return "❌ Battle arena is not running"
                
                # Check health endpoint
                import requests
                try:
                    health_response = requests.get("http://localhost:8080/health", timeout=5)
                    if health_response.status_code == 200:
                        health_data = health_response.json()
                    else:
                        health_data = {"status": "unhealthy"}
                except:
                    health_data = {"status": "unreachable"}
                
                # Check service manager
                try:
                    services_response = requests.get("http://localhost:9000/services", timeout=5)
                    if services_response.status_code == 200:
                        services = services_response.json()
                        active_services = len([s for s in services.values() if s.get("status") == "running"])
                    else:
                        active_services = 0
                except:
                    active_services = 0
                
                # Calculate battle progress
                if self.battle_start_time:
                    elapsed = time.time() - self.battle_start_time
                    remaining = max(0, self.battle_duration - elapsed)
                    progress = min(100, (elapsed / self.battle_duration) * 100)
                else:
                    elapsed = 0
                    remaining = self.battle_duration
                    progress = 0
                
                status_report = {
                    "battle_id": self.battle_id,
                    "arena_status": health_data.get("status", "unknown"),
                    "active_services": active_services,
                    "elapsed_time": f"{elapsed:.1f}s",
                    "remaining_time": f"{remaining:.1f}s",
                    "progress_percent": f"{progress:.1f}%",
                    "red_agents": self.red_agents
                }
                
                return f"📊 Battle Status Report:\n{json.dumps(status_report, indent=2)}"
                
            except Exception as e:
                return f"❌ Error monitoring battle: {str(e)}"
        
        return monitor_battle_progress

    def _create_agent_communication_tool(self):
        @function_tool(name_override="send_message_to_red_agent")
        async def send_message_to_red_agent(agent_id: str, message: str, agent_url: str = None) -> str:
            """
            Send a message to a specific red agent.
            If agent_url is not provided, will try to find the agent based on agent_id.
            """
            try:
                if not agent_url:
                    # Try to find agent URL based on agent_id
                    if agent_id == "red_agent_0":
                        agent_url = "http://localhost:8001"
                    elif agent_id == "red_agent_1":
                        agent_url = "http://localhost:8002"
                    else:
                        return f"❌ Unknown agent ID: {agent_id}"
                
                client = await self._make_client(agent_url)
                params = MessageSendParams(
                    message=Message(
                        role=Role.user,
                        parts=[Part(TextPart(text=message))],
                        messageId=uuid4().hex,
                        taskId=uuid4().hex,
                    )
                )
                req = SendStreamingMessageRequest(id=str(uuid4()), params=params)
                chunks: List[str] = []
                async for chunk in client.send_message_streaming(req):
                    if not isinstance(chunk.root, SendStreamingMessageSuccessResponse):
                        continue
                    event = chunk.root.result
                    if isinstance(event, TaskArtifactUpdateEvent):
                        for p in event.artifact.parts:
                            if isinstance(p.root, TextPart):
                                chunks.append(p.root.text)
                    elif isinstance(event, TaskStatusUpdateEvent):
                        msg = event.status.message
                        if msg:
                            for p in msg.parts:
                                if isinstance(p.root, TextPart):
                                    chunks.append(p.root.text)
                
                response = "".join(chunks).strip() or "No response from agent."
                return f"✅ Message sent to {agent_id}:\nResponse: {response}"
                
            except Exception as e:
                return f"❌ Error communicating with {agent_id}: {str(e)}"
        
        return send_message_to_red_agent

    def _create_battle_control_tool(self):
        @function_tool(name_override="start_battle")
        def start_battle(battle_duration_minutes: int = 5) -> str:
            """
            Start the battle royale with the specified duration.
            """
            self.logger.info(f"Starting battle: duration={battle_duration_minutes} minutes")
            
            try:
                self.battle_start_time = time.time()
                self.battle_duration = battle_duration_minutes * 60
                
                # Log battle start event
                self.battle_log.append({
                    "timestamp": time.time(),
                    "event": "battle_started",
                    "duration_minutes": battle_duration_minutes,
                    "battle_id": self.battle_id
                })
                
                # Send start message to all red agents
                start_message = f"Battle royale has begun! You have {battle_duration_minutes} minutes to create and maintain your web service on port 80. Good luck!"
                
                self.logger.info(f"Battle started successfully: {battle_duration_minutes} minutes")
                return f"🎯 Battle started! Duration: {battle_duration_minutes} minutes\nStart message: {start_message}"
                
            except Exception as e:
                self.logger.error(f"Error starting battle: {str(e)}")
                return f"❌ Error starting battle: {str(e)}"
        
        return start_battle

    def _create_uptime_tracking_tool(self):
        @function_tool(name_override="calculate_uptime_percentages")
        def calculate_uptime_percentages() -> str:
            """
            Calculate uptime percentages for all agents during the battle.
            This checks each agent's web service and updates the uptime tracking data.
            """
            self.logger.info("Calculating uptime percentages for all agents")
            
            try:
                if not self.battle_start_time:
                    self.logger.warning("Uptime calculation requested but battle has not started")
                    return "❌ Battle has not started yet"
                
                # Check each red agent's service
                for agent_id in self.red_agents:
                    if agent_id not in self.uptime_data:
                        self.uptime_data[agent_id] = {"total_checks": 0, "successful_checks": 0}
                    
                    # Determine agent URL
                    agent_url = None
                    if agent_id == "red_agent_0":
                        agent_url = "http://localhost:8001"
                    elif agent_id == "red_agent_1":
                        agent_url = "http://localhost:8002"
                    elif agent_id == "red_agent_2":
                        agent_url = "http://localhost:8003"
                    else:
                        continue
                    
                    # Check if agent's service is running on port 80
                    try:
                        import requests
                        # Check if port 80 is being used by this agent
                        response = requests.get(f"http://localhost:80", timeout=5)
                        self.uptime_data[agent_id]["total_checks"] += 1
                        
                        if response.status_code == 200:
                            self.uptime_data[agent_id]["successful_checks"] += 1
                            status = "✅ Online"
                            self.logger.info(f"Agent {agent_id} service is online")
                        else:
                            status = "❌ Offline"
                            self.logger.warning(f"Agent {agent_id} service returned status {response.status_code}")
                    except:
                        self.uptime_data[agent_id]["total_checks"] += 1
                        status = "❌ Offline"
                        self.logger.warning(f"Agent {agent_id} service is offline")
                    
                    # Log the check
                    check_event = {
                        "timestamp": time.time(),
                        "agent_id": agent_id,
                        "status": status,
                        "elapsed_time": time.time() - self.battle_start_time
                    }
                    self.battle_log.append(check_event)
                    self.logger.info(f"Uptime check: {agent_id} = {status}")
                
                # Calculate percentages
                uptime_report = {}
                for agent_id, data in self.uptime_data.items():
                    if data["total_checks"] > 0:
                        percentage = (data["successful_checks"] / data["total_checks"]) * 100
                        uptime_report[agent_id] = {
                            "uptime_percentage": f"{percentage:.1f}%",
                            "successful_checks": data["successful_checks"],
                            "total_checks": data["total_checks"]
                        }
                        self.logger.info(f"Agent {agent_id} uptime: {percentage:.1f}% ({data['successful_checks']}/{data['total_checks']})")
                    else:
                        uptime_report[agent_id] = {
                            "uptime_percentage": "0.0%",
                            "successful_checks": 0,
                            "total_checks": 0
                        }
                
                self.logger.info("Uptime calculation completed")
                return f"📊 Uptime Report:\n{json.dumps(uptime_report, indent=2)}"
                
            except Exception as e:
                self.logger.error(f"Error calculating uptime: {str(e)}")
                return f"❌ Error calculating uptime: {str(e)}"
        
        return calculate_uptime_percentages

    def _create_winner_determination_tool(self):
        @function_tool(name_override="determine_winner")
        def determine_winner() -> str:
            """
            Determine the winner of the battle royale based on uptime percentages.
            """
            try:
                if not self.battle_start_time:
                    return "❌ Battle has not started yet"
                
                # Calculate current uptime percentages
                uptime_report = {}
                for agent_id, data in self.uptime_data.items():
                    if data["total_checks"] > 0:
                        percentage = (data["successful_checks"] / data["total_checks"]) * 100
                        uptime_report[agent_id] = percentage
                    else:
                        uptime_report[agent_id] = 0.0
                
                if not uptime_report:
                    return "❌ No uptime data available"
                
                # Find the winner
                winner = max(uptime_report.items(), key=lambda x: x[1])
                winner_id, winner_percentage = winner
                
                # Check if battle is still ongoing
                elapsed = time.time() - self.battle_start_time
                remaining = max(0, self.battle_duration - elapsed)
                
                if remaining > 0:
                    status = f"🏆 Current Leader: {winner_id} ({winner_percentage:.1f}% uptime)\n⏱️ Battle still ongoing - {remaining:.1f}s remaining"
                else:
                    status = f"🏆 WINNER: {winner_id} ({winner_percentage:.1f}% uptime)\n🎯 Battle completed!"
                
                # Add all rankings
                rankings = sorted(uptime_report.items(), key=lambda x: x[1], reverse=True)
                ranking_text = "\n📈 Final Rankings:\n"
                for i, (agent_id, percentage) in enumerate(rankings, 1):
                    ranking_text += f"{i}. {agent_id}: {percentage:.1f}%\n"
                
                return status + ranking_text
                
            except Exception as e:
                return f"❌ Error determining winner: {str(e)}"
        
        return determine_winner

    def _create_battle_summary_tool(self):
        @function_tool(name_override="generate_battle_summary")
        def generate_battle_summary() -> str:
            """
            Generate a comprehensive summary of the battle royale.
            """
            try:
                if not self.battle_id:
                    return "❌ No battle has been created yet"
                
                # Calculate final uptime percentages
                uptime_report = {}
                for agent_id, data in self.uptime_data.items():
                    if data["total_checks"] > 0:
                        percentage = (data["successful_checks"] / data["total_checks"]) * 100
                        uptime_report[agent_id] = percentage
                    else:
                        uptime_report[agent_id] = 0.0
                
                # Determine winner
                winner = None
                if uptime_report:
                    winner = max(uptime_report.items(), key=lambda x: x[1])
                
                # Calculate battle statistics
                elapsed = 0
                if self.battle_start_time:
                    elapsed = time.time() - self.battle_start_time
                
                total_events = len(self.battle_log)
                successful_services = sum(1 for event in self.battle_log if "✅" in event.get("status", ""))
                
                # Generate summary
                summary = {
                    "battle_id": self.battle_id,
                    "duration": f"{elapsed:.1f} seconds",
                    "total_agents": len(self.red_agents),
                    "total_events_logged": total_events,
                    "successful_service_checks": successful_services,
                    "winner": winner[0] if winner else "None",
                    "winner_uptime": f"{winner[1]:.1f}%" if winner else "N/A",
                    "all_uptime_percentages": uptime_report,
                    "battle_status": "Completed" if elapsed >= self.battle_duration else "Ongoing"
                }
                
                return f"📋 Battle Summary:\n{json.dumps(summary, indent=2)}"
                
            except Exception as e:
                return f"❌ Error generating battle summary: {str(e)}"
        
        return generate_battle_summary

    async def invoke(self, context) -> str:
        print(context.get_user_input(), "=========================================GREEN INPUT")
        await self.ensure_mcp_connected()
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(),
            "role": "user"
        }]
        result = await Runner.run(
            self.main_agent,
            query_ctx,
            max_turns=30,
            run_config=RunConfig(model_provider=CUSTOM_MODEL_PROVIDER)
        )  # type: ignore
        self.chat_history = result.to_input_list()  # type: ignore
        print(result.final_output, "=========================================GREEN OUTPUT")
        return result.final_output

class GreenAgentExecutor(AgentExecutor):
    def __init__(self, mcp_url: str = None) -> None:
        """Initialize the Green Agent Executor."""
        self.green_agent = GreenAgent(mcp_url=mcp_url)

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
        reply_text = await self.green_agent.invoke(context)
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