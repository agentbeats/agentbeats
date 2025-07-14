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
import threading
import queue

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
        self.red_agents = []  # List of agent IDs like ["red_agent_0", "red_agent_1", "red_agent_2"]
        self.agent_urls = {}  # Map of agent_id to actual URL from backend
        self.battle_start_time = None
        self.battle_duration = 60  # 1 minute default
        self.monitoring_interval = 5  # 5 seconds for frequent logging
        
        # Agent identifiers
        self.agent_identifiers = {}  # {agent_id: unique_identifier}
        
        # Uptime tracking
        self.uptime_data = {}  # {agent_id: {total_checks: int, successful_checks: int}}
        self.battle_log = []  # List of battle events
        
        # Background monitoring
        self.monitoring_thread = None
        self.monitoring_active = False

        # Initialize chat history and tools
        self.chat_history: List[Dict[str, str]] = []
        self.tool_list = [
            self._create_start_battle_tool(),
            self._create_retrieve_final_result_tool(),
            self._create_test_message_tool(),
        ]

    def _setup_logging(self):
        """Setup logging configuration for the battle royale"""
        # Configure logging to send to backend server
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()  # Only log to console for debugging
            ]
        )
        
        # Create a specific logger for battle royale
        logger = logging.getLogger("battle_royale_green_agent")
        logger.setLevel(logging.INFO)
        
        # Add console handler with more visible formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('🟢 [GREEN AGENT] %(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Log initial setup
        logger.info("Battle Royale logging system initialized - logs will be sent to backend server")
        print("🟢 [GREEN AGENT] Logging system ready - logs will be sent to backend server!")

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
        def create_battle_arena(battle_id: str, num_red_agents: int = 3) -> str:
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
                # Get current battle status
                elapsed = time.time() - self.battle_start_time if self.battle_start_time else 0
                remaining = max(0, self.battle_duration - elapsed) if self.battle_duration else 0
                
                # Calculate uptime percentages
                uptime_report = {}
                for agent_id, data in self.uptime_data.items():
                    if data["total_checks"] > 0:
                        percentage = (data["successful_checks"] / data["total_checks"]) * 100
                        uptime_report[agent_id] = f"{percentage:.1f}%"
                    else:
                        uptime_report[agent_id] = "0.0%"
                
                # Build status report
                status_report = {
                    "battle_active": self.battle_start_time is not None,
                    "elapsed_seconds": elapsed,
                    "remaining_seconds": remaining,
                    "battle_duration_minutes": self.battle_duration / 60 if self.battle_duration else 0,
                    "uptime_percentages": uptime_report,
                    "total_checks": sum(data["total_checks"] for data in self.uptime_data.values()),
                    "arena_status": "active",
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
                        agent_url = "http://localhost:8021"
                    elif agent_id == "red_agent_2":
                        agent_url = "http://localhost:8031"
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
        def start_battle() -> str:
            """
            Start the battle royale with the default duration (1 minute).
            """
            battle_duration_minutes = 1  # 1 minute
            self.logger.info(f"Starting battle: duration={battle_duration_minutes} minute")
            
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
                
                # Start background monitoring
                self._start_background_monitoring()
                
                # Send start message to all red agents
                start_message = f"Battle royale has begun! You have {battle_duration_minutes} minutes to create and maintain your web service on port 80. Good luck!"
                
                self.logger.info(f"Battle started successfully: {battle_duration_minutes} minutes with automatic monitoring every 15 seconds")
                return f"🎯 Battle started! Duration: {battle_duration_minutes} minutes\nStart message: {start_message}\n📊 Automatic monitoring started (every 15 seconds)"
                
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
                        agent_url = "http://localhost:8021"
                    elif agent_id == "red_agent_2":
                        agent_url = "http://localhost:8031"
                    else:
                        continue
                    
                    # Check if agent's service is running on port 80
                    try:
                        import requests
                        # Check if port 8081 (mapped from container port 80) is being used by this agent
                        response = requests.get(f"http://localhost:8081", timeout=5)
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

    def _create_agent_identifier_tool(self):
        @function_tool(name_override="generate_agent_identifiers")
        def generate_agent_identifiers() -> str:
            """
            Generate unique identifiers for each red agent and send them to the agents.
            This helps distinguish between agents when they're running the same service.
            """
            try:
                if not self.red_agents:
                    return "❌ No red agents defined. Create battle arena first."
                
                # Generate unique identifiers for each agent
                import random
                import string
                
                identifiers = {}
                for agent_id in self.red_agents:
                    # Generate a unique 8-character identifier
                    identifier = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    identifiers[agent_id] = identifier
                
                self.agent_identifiers = identifiers
                
                # Send identifiers to each agent
                messages_sent = []
                for agent_id, identifier in identifiers.items():
                    message = f"Your unique identifier for this battle is: {identifier}. Please include this identifier in your web service response so I can identify which agent is serving on port 80."
                    
                    # Send message to agent
                    try:
                        # Determine agent URL
                        agent_url = None
                        if agent_id == "red_agent_0":
                            agent_url = "http://localhost:8001"
                        elif agent_id == "red_agent_1":
                            agent_url = "http://localhost:8021"
                        elif agent_id == "red_agent_2":
                            agent_url = "http://localhost:8031"
                        else:
                            continue
                        
                        # Create a simple HTTP request to send the message
                        import requests
                        import json
                        
                        # Send identifier via HTTP POST (assuming agents have an endpoint to receive this)
                        payload = {
                            "message": message,
                            "identifier": identifier,
                            "agent_id": agent_id
                        }
                        
                        try:
                            response = requests.post(f"{agent_url}/receive_identifier", json=payload, timeout=5)
                            if response.status_code == 200:
                                messages_sent.append(f"✅ {agent_id}: {identifier}")
                            else:
                                messages_sent.append(f"⚠️ {agent_id}: {identifier} (HTTP {response.status_code})")
                        except:
                            # If POST fails, try to send via the A2A client
                            messages_sent.append(f"📤 {agent_id}: {identifier} (sent via A2A)")
                            
                    except Exception as e:
                        messages_sent.append(f"❌ {agent_id}: {identifier} (error: {str(e)})")
                
                self.logger.info(f"Generated identifiers: {identifiers}")
                return f"🎯 Agent Identifiers Generated:\n" + "\n".join(messages_sent) + f"\n\n📋 Identifiers: {json.dumps(identifiers, indent=2)}"
                
            except Exception as e:
                self.logger.error(f"Error generating agent identifiers: {str(e)}")
                return f"❌ Error generating agent identifiers: {str(e)}"
        
        return generate_agent_identifiers

    def _auto_initialize_battle_system(self):
        """Automatically initialize the battle arena and prepare all systems."""
        try:
            print(f"🔍 DEBUG: Starting _auto_initialize_battle_system")
            print(f"🔍 DEBUG: Current agent_urls: {self.agent_urls}")
            print(f"🔍 DEBUG: Current red_agents: {self.red_agents}")
            
            self.logger.info("🔄 Auto-initializing battle system...")
            
            # 1. Create battle arena
            print(f"🔍 DEBUG: Calling _create_battle_arena_auto")
            self._create_battle_arena_auto()
            
            # 2. Generate agent identifiers
            print(f"🔍 DEBUG: Calling _generate_agent_identifiers_auto")
            self._generate_agent_identifiers_auto()
            
            # 3. Provide SSH credentials to all agents
            print(f"🔍 DEBUG: Calling _provide_ssh_credentials_auto")
            self._provide_ssh_credentials_auto()
            
            print(f"🔍 DEBUG: _auto_initialize_battle_system completed")
            print(f"🔍 DEBUG: Final agent_urls: {self.agent_urls}")
            print(f"🔍 DEBUG: Final red_agents: {self.red_agents}")
            
            self.logger.info("✅ Battle system auto-initialization complete!")
            
        except Exception as e:
            print(f"❌ DEBUG: Error in _auto_initialize_battle_system: {e}")
            self.logger.error(f"❌ Auto-initialization failed: {str(e)}")

    def _create_battle_arena_auto(self):
        """Automatically create the battle arena."""
        try:
            self.logger.info("🏗️ Creating battle arena...")
            
            # Change to docker directory
            docker_dir = Path(__file__).parent.parent.parent / "docker"
            os.chdir(docker_dir)
            
            # Stop any existing containers
            subprocess.run(["docker-compose", "down"], capture_output=True)
            
            # Start the battle arena
            result = subprocess.run(
                ["docker-compose", "up", "-d", "--build"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                # Don't set red_agents here - they should come from backend notification
                # Don't set battle_id here - it should come from backend notification
                self.logger.info("✅ Battle arena created")
                print("✅ Battle arena created - waiting for battle_id and agent URLs from backend")
            else:
                raise Exception(f"Failed to create battle arena: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"❌ Battle arena creation failed: {str(e)}")
            raise

    def _generate_agent_identifiers_auto(self):
        """Automatically generate identifiers for all agents."""
        try:
            self.logger.info("🆔 Generating agent identifiers...")
            
            import random
            import string
            
            self.agent_identifiers = {}
            for agent_id in self.red_agents:
                identifier = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                self.agent_identifiers[agent_id] = identifier
            
            self.logger.info(f"✅ Agent identifiers generated: {self.agent_identifiers}")
            
        except Exception as e:
            self.logger.error(f"❌ Agent identifier generation failed: {str(e)}")
            raise

    def _provide_ssh_credentials_auto(self):
        """Automatically provide SSH credentials and identifiers to all agents."""
        try:
            print(f"🔍 DEBUG: Starting _provide_ssh_credentials_auto")
            print(f"🔍 DEBUG: Available agent_urls: {self.agent_urls}")
            print(f"🔍 DEBUG: Red agents list: {self.red_agents}")
            print(f"🔍 DEBUG: Agent identifiers: {self.agent_identifiers}")
            
            self.logger.info("🔑 Providing SSH credentials and identifiers to all agents...")
            
            ssh_credentials = {
                "host": "localhost",
                "port": 2222,
                "username": "battle",
                "password": "battle123"
            }
            
            # Send SSH credentials and identifiers to all red agents
            for agent_id in self.red_agents:
                print(f"🔍 DEBUG: Sending credentials to agent_id: {agent_id}")
                
                # Get the agent's unique identifier
                identifier = self.agent_identifiers.get(agent_id, "UNKNOWN")
                
                message = f"""Connect to the battle arena and set up your service:

SSH Credentials:
- Host: {ssh_credentials['host']}
- Port: {ssh_credentials['port']}
- Username: {ssh_credentials['username']}
- Password: {ssh_credentials['password']}

Your unique identifier: {identifier}

Steps:
1. Use the set_agent_identifier tool to set your identifier: {identifier}
2. Use the SSH Connect tool to connect to the battle arena
3. Use the Create Web Service tool to start your service on port 80
4. Make sure your service displays your identifier: {identifier}

This will ensure the monitoring system can identify your service correctly."""
                
                print(f"🔍 DEBUG: Full message for {agent_id}: {message}")
                
                # Send the message with retry logic
                result = self._send_message_to_agent_auto_with_retry(agent_id, message)
                print(f"🔍 DEBUG: Credentials send result for {agent_id}: {result}")
                
                if result and not result.startswith("Failed"):
                    self.logger.info(f"✅ Credentials sent to {agent_id}")
                else:
                    self.logger.error(f"❌ Failed to send credentials to {agent_id}")
            
            print(f"🔍 DEBUG: _provide_ssh_credentials_auto completed")
            
        except Exception as e:
            print(f"❌ DEBUG: Error in _provide_ssh_credentials_auto: {e}")
            self.logger.error(f"❌ Error providing credentials: {e}")

    def _create_start_battle_tool(self):
        @function_tool(name_override="start_battle_royale")
        def start_battle_royale() -> str:
            """
            Start the battle royale. This single command will:
            1. Initialize the battle arena and agents
            2. Start the 2-minute battle timer
            3. Begin automatic monitoring every 5 seconds
            4. Send battle start signals to all red agents
            5. Log all events to the MCP server
            6. Track uptime and determine the winner automatically
            """
            try:
                print(f"🔍 DEBUG: Starting start_battle_royale function")
                print(f"🔍 DEBUG: Battle ID: {self.battle_id}")
                print(f"🔍 DEBUG: Agent URLs: {self.agent_urls}")
                print(f"🔍 DEBUG: Red agents: {self.red_agents}")
                
                # If agent URLs are not set up (manual testing), set them up manually
                if not self.agent_urls or not self.red_agents:
                    print(f"🔍 DEBUG: Setting up agent URLs manually for testing")
                    self.agent_urls = {
                        "red_agent_0": "http://localhost:8001",
                        "red_agent_1": "http://localhost:8021", 
                        "red_agent_2": "http://localhost:8031"
                    }
                    self.red_agents = ["red_agent_0", "red_agent_1", "red_agent_2"]
                    print(f"🔍 DEBUG: Manual setup complete - Agent URLs: {self.agent_urls}")
                    print(f"🔍 DEBUG: Manual setup complete - Red agents: {self.red_agents}")
                
                self.logger.info("🎯 Starting Battle Royale!")
                
                # Initialize battle system first (now with populated red_agents)
                print(f"🔍 DEBUG: Calling _auto_initialize_battle_system")
                self.logger.info("🔄 Initializing battle system...")
                self._auto_initialize_battle_system()
                
                # Set battle parameters
                battle_duration_minutes = 2
                self.battle_start_time = time.time()
                self.battle_duration = battle_duration_minutes * 60
                
                print(f"🔍 DEBUG: Battle duration set to {battle_duration_minutes} minutes")
                
                # Log battle start
                self.battle_log.append({
                    "timestamp": time.time(),
                    "event": "battle_started",
                    "duration_minutes": battle_duration_minutes,
                    "battle_id": self.battle_id
                })
                self._send_log_to_backend(f"Battle started! Duration: {battle_duration_minutes} minutes")
                
                # Start background monitoring
                print(f"🔍 DEBUG: Starting background monitoring")
                self._start_background_monitoring()
                
                # Send start message to all red agents concurrently
                start_message = f"Battle royale has begun! You have {battle_duration_minutes} minutes to create and maintain your web service on port 80. Good luck!"
                
                print(f"🔍 DEBUG: Sending start messages to red agents: {self.red_agents}")
                
                # Check agent readiness first
                ready_agents = []
                for agent_id in self.red_agents:
                    agent_url = self.agent_urls.get(agent_id)
                    if agent_url:
                        ready_agents.append(agent_id)
                        print(f"✅ DEBUG: {agent_id} is ready for battle start")
                    else:
                        print(f"❌ DEBUG: {agent_id} has no URL configured")
                
                if not ready_agents:
                    self.logger.warning("⚠️ No agents are ready for battle start")
                
                # Send to all ready agents concurrently with retry logic
                import concurrent.futures
                print(f"🔍 DEBUG: Sending battle start messages concurrently to {ready_agents}")
                
                battle_start_results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(ready_agents)) as executor:
                    # Submit all tasks
                    future_to_agent = {
                        executor.submit(self._send_message_to_agent_auto_with_retry, agent_id, start_message): agent_id 
                        for agent_id in ready_agents
                    }
                    
                    # Collect results as they complete
                    for future in concurrent.futures.as_completed(future_to_agent, timeout=45):
                        agent_id = future_to_agent[future]
                        try:
                            result = future.result()
                            print(f"🔍 DEBUG: Battle start result for {agent_id}: {result}")
                            battle_start_results.append(f"{agent_id}: {result}")
                        except concurrent.futures.TimeoutError:
                            print(f"❌ DEBUG: {agent_id} timed out during battle start")
                            battle_start_results.append(f"{agent_id}: Timeout during battle start")
                        except Exception as e:
                            print(f"❌ DEBUG: {agent_id} failed during battle start: {e}")
                            battle_start_results.append(f"{agent_id}: Error during battle start - {e}")
                
                self.logger.info(f"Battle start messages sent: {battle_start_results}")
                
                print(f"🔍 DEBUG: start_battle_royale completed successfully")
                self.logger.info(f"✅ Battle started! Duration: {battle_duration_minutes} minutes")
                return f"🎯 Battle Royale Started!\n⏱️ Duration: {battle_duration_minutes} minutes\n📊 Auto-monitoring: Every 5 seconds\n🤖 Agents: {len(self.red_agents)} red agents\n🏆 Winner will be determined automatically!"
                
            except Exception as e:
                print(f"❌ DEBUG: Error in start_battle_royale: {e}")
                self.logger.error(f"❌ Error starting battle: {str(e)}")
                return f"❌ Error starting battle: {str(e)}"
        
        return start_battle_royale

    def _send_message_to_agent_auto(self, agent_id: str, message: str):
        """Automatically send a message to a specific agent."""
        try:
            print(f"🔍 DEBUG: Starting _send_message_to_agent_auto for agent_id: {agent_id}")
            print(f"🔍 DEBUG: Available agent_urls: {self.agent_urls}")
            
            # Get agent URL from the backend-provided mapping
            agent_url = self.agent_urls.get(agent_id)
            if not agent_url:
                print(f"❌ DEBUG: No URL found for agent {agent_id}. Available agents: {list(self.agent_urls.keys())}")
                self.logger.error(f"❌ No URL found for agent {agent_id}. Available agents: {list(self.agent_urls.keys())}")
                return None
            
            print(f"🔍 DEBUG: Found agent_url for {agent_id}: {agent_url}")
            print(f"🔍 DEBUG: Message to send: {message}")
            
            # Use threading to run the async function
            print(f"🔍 DEBUG: Using threading to run async function")
            result_queue = queue.Queue()
            
            def run_async_in_thread():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(self._send_message_async(agent_url, message))
                    result_queue.put(result)
                except Exception as e:
                    result_queue.put(f"Error: {e}")
                finally:
                    loop.close()
            
            # Start the thread
            thread = threading.Thread(target=run_async_in_thread)
            thread.start()
            thread.join(timeout=10)  # Wait up to 10 seconds
            
            # Get the result
            try:
                result = result_queue.get_nowait()
                print(f"🔍 DEBUG: Thread completed with result: {result}")
                return result
            except queue.Empty:
                print(f"❌ DEBUG: Thread timed out")
                return None
            
        except Exception as e:
            print(f"❌ DEBUG: Error in _send_message_to_agent_auto: {e}")
            self.logger.error(f"❌ Error sending message to {agent_id}: {e}")
            return None

    async def _send_message_async(self, agent_url: str, message: str):
        """Async function to send message - exactly like the working test script"""
        try:
            print(f"🔍 DEBUG: Starting async send_message to {agent_url}")
            
            # First check if agent is reachable
            import requests
            try:
                print(f"🔍 DEBUG: Checking health of {agent_url}")
                health_check = requests.get(f"{agent_url}/.well-known/agent.json", timeout=5)
                print(f"🔍 DEBUG: Health check response: {health_check.status_code}")
                if health_check.status_code != 200:
                    print(f"❌ DEBUG: Agent at {agent_url} is not healthy (status: {health_check.status_code})")
                    return None
            except Exception as e:
                print(f"❌ DEBUG: Health check failed for {agent_url}: {e}")
                return None
            
            # Create A2A client using the existing method
            print(f"🔍 DEBUG: Creating A2A client for {agent_url}")
            try:
                a2a_client = await self._make_client(agent_url)
                print(f"🔍 DEBUG: A2A client created successfully")
            except Exception as e:
                print(f"❌ DEBUG: Failed to create A2A client: {e}")
                return None
            
            # Send the message using proper A2A format
            print(f"🔍 DEBUG: Sending message via A2A to {agent_url}")
            print(f"🔍 DEBUG: Message content: {message}")
            try:
                params = MessageSendParams(
                    message=Message(
                        role=Role.user,
                        parts=[Part(TextPart(text=message))],
                        messageId=uuid4().hex,
                        taskId=uuid4().hex,
                    )
                )
                req = SendStreamingMessageRequest(id=str(uuid4()), params=params)
                print(f"🔍 DEBUG: Created request object")
                
                chunks = []
                print(f"🔍 DEBUG: Starting streaming message...")
                async for chunk in a2a_client.send_message_streaming(req):
                    print(f"🔍 DEBUG: Received chunk: {type(chunk)}")
                    if not isinstance(chunk.root, SendStreamingMessageSuccessResponse):
                        print(f"🔍 DEBUG: Skipping non-success chunk")
                        continue
                    event = chunk.root.result
                    print(f"🔍 DEBUG: Event type: {type(event)}")
                    if isinstance(event, TaskArtifactUpdateEvent):
                        for p in event.artifact.parts:
                            if isinstance(p.root, TextPart):
                                chunks.append(p.root.text)
                                print(f"🔍 DEBUG: Added artifact text: {p.root.text}")
                    elif isinstance(event, TaskStatusUpdateEvent):
                        msg = event.status.message
                        if msg:
                            for p in msg.parts:
                                if isinstance(p.root, TextPart):
                                    chunks.append(p.root.text)
                                    print(f"🔍 DEBUG: Added status text: {p.root.text}")
                
                response = "".join(chunks).strip() or "No response from agent."
                print(f"🔍 DEBUG: A2A response received: {response}")
                
                self.logger.info(f"✅ Message sent to {agent_url}: {response}")
                return response
                
            except Exception as e:
                print(f"❌ DEBUG: Error in message sending/streaming: {e}")
                import traceback
                traceback.print_exc()
                return None
            
        except Exception as e:
            print(f"❌ DEBUG: Error in async send_message: {e}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"❌ Failed to send message to {agent_url}: {e}")
            return None

    def _create_ssh_credentials_tool(self):
        @function_tool(name_override="provide_ssh_credentials_to_all_agents")
        def provide_ssh_credentials_to_all_agents() -> str:
            """
            Automatically provide SSH credentials to all red agents at once.
            This ensures all agents can connect to the battle arena simultaneously.
            """
            try:
                if not self.red_agents:
                    return "❌ No red agents defined. Create battle arena first."
                
                ssh_credentials = {
                    "host": "localhost",
                    "port": 2222,
                    "username": "battle",
                    "password": "battle123"
                }
                
                # Send SSH credentials to all red agents simultaneously
                messages_sent = []
                for agent_id in self.red_agents:
                    message = f"Connect to the battle arena using these SSH credentials: Host: {ssh_credentials['host']}, Port: {ssh_credentials['port']}, Username: {ssh_credentials['username']}, Password: {ssh_credentials['password']}. Use the connect_to_battle_arena tool immediately."
                    
                    # Send message to agent
                    try:
                        # Determine agent URL
                        agent_url = None
                        if agent_id == "red_agent_0":
                            agent_url = "http://localhost:8001"
                        elif agent_id == "red_agent_1":
                            agent_url = "http://localhost:8021"
                        elif agent_id == "red_agent_2":
                            agent_url = "http://localhost:8031"
                        else:
                            continue
                        
                        # Send via A2A client
                        import asyncio
                        
                        async def send_ssh_credentials():
                            try:
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
                                return f"✅ {agent_id}: SSH credentials sent successfully"
                            except Exception as e:
                                return f"❌ {agent_id}: Failed to send SSH credentials - {str(e)}"
                        
                        # Run the async function
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(send_ssh_credentials())
                            messages_sent.append(result)
                        finally:
                            loop.close()
                            
                    except Exception as e:
                        messages_sent.append(f"❌ {agent_id}: Error sending SSH credentials - {str(e)}")
                
                self.logger.info(f"SSH credentials sent to all agents: {messages_sent}")
                return f"🔑 SSH Credentials Sent to All Agents:\n" + "\n".join(messages_sent) + f"\n\n📋 Credentials: {json.dumps(ssh_credentials, indent=2)}"
                
            except Exception as e:
                self.logger.error(f"Error providing SSH credentials: {str(e)}")
                return f"❌ Error providing SSH credentials: {str(e)}"
        
        return provide_ssh_credentials_to_all_agents

    def _start_background_monitoring(self):
        """Start background monitoring thread that runs every 15 seconds."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return  # Already running
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._background_monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Background monitoring started (every 5 seconds)")
        self.final_judgement = None  # Reset final judgement at start

    def _stop_background_monitoring(self):
        """Stop background monitoring thread."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Background monitoring stopped")

    def _background_monitoring_loop(self):
        """Background monitoring loop that runs every 15 seconds."""
        while self.monitoring_active:
            try:
                elapsed = time.time() - self.battle_start_time if self.battle_start_time else 0
                if self.battle_start_time and elapsed >= self.battle_duration:
                    # Stop monitoring and judge the battle
                    self.monitoring_active = False
                    self.logger.info("⏰ Battle time is up! Judging the results...")
                    self._judge_and_finalize_battle()
                    break
                self._perform_monitoring_check()
                
                # Log to MCP server if connected
                if self.mcp_servers_connected:
                    self._log_to_mcp_server()
                
                # Sleep for 5 seconds
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in background monitoring: {str(e)}")
                time.sleep(5)  # Continue even if there's an error

    def _perform_monitoring_check(self):
        """Perform a single monitoring check."""
        if not self.battle_start_time:
            return  # Battle not started yet
        
        try:
            # Check port 8081 in the Docker container to see which agent's service is running
            try:
                import requests
                # Check the Docker container's port 80 (mapped to host port 8081)
                response = requests.get("http://localhost:8081", timeout=5)
                
                if response.status_code == 200:
                    # Service is running, check which agent it belongs to
                    service_content = response.text.strip()
                    print(f"🔍 DEBUG: Service content on port 8081: {service_content}")
                    print(f"🔍 DEBUG: Looking for identifiers: {self.agent_identifiers}")
                    
                    active_agent = None
                    
                    # Check which agent's identifier is being served
                    for agent_id, identifier in self.agent_identifiers.items():
                        print(f"🔍 DEBUG: Checking if '{identifier}' is in service content")
                        if identifier in service_content:
                            active_agent = agent_id
                            print(f"🔍 DEBUG: Found identifier '{identifier}' for agent {agent_id}")
                            break
                    
                    # Fallback: check for agent names if no identifiers found
                    if not active_agent:
                        print(f"🔍 DEBUG: No identifiers found, checking agent names")
                        for agent_id in self.red_agents:
                            if agent_id in service_content:
                                active_agent = agent_id
                                print(f"🔍 DEBUG: Found agent name '{agent_id}' in service content")
                                break
                    
                    if active_agent:
                        # Update uptime for the active agent
                        if active_agent not in self.uptime_data:
                            self.uptime_data[active_agent] = {"total_checks": 0, "successful_checks": 0}
                        self.uptime_data[active_agent]["total_checks"] += 1
                        self.uptime_data[active_agent]["successful_checks"] += 1
                        
                        # Update all other agents as offline for this check
                        for agent_id in self.red_agents:
                            if agent_id != active_agent:
                                if agent_id not in self.uptime_data:
                                    self.uptime_data[agent_id] = {"total_checks": 0, "successful_checks": 0}
                                self.uptime_data[agent_id]["total_checks"] += 1
                        
                        # Log the check
                        check_event = {
                            "timestamp": time.time(),
                            "active_agent": active_agent,
                            "service_content": service_content,
                            "elapsed_time": time.time() - self.battle_start_time,
                            "source": "background_monitoring"
                        }
                        self.battle_log.append(check_event)
                        
                        # Log current uptime percentages
                        for agent_id in self.red_agents:
                            data = self.uptime_data[agent_id]
                            if data["total_checks"] > 0:
                                percentage = (data["successful_checks"] / data["total_checks"]) * 100
                                status = "✅ Active" if agent_id == active_agent else "❌ Blocked"
                                print(f"📊 {agent_id}: {status} ({percentage:.1f}%)")
                    else:
                        # Service running but can't identify which agent
                        self.logger.warning(f"Service running on port 8081 but can't identify agent. Content: {service_content}")
                        
                else:
                    # No service running on port 80
                    print(f"🔍 DEBUG: No service running on port 8081 (status code: {response.status_code})")
                    for agent_id in self.red_agents:
                        if agent_id not in self.uptime_data:
                            self.uptime_data[agent_id] = {"total_checks": 0, "successful_checks": 0}
                        self.uptime_data[agent_id]["total_checks"] += 1
                    
                    check_event = {
                        "timestamp": time.time(),
                        "active_agent": None,
                        "service_content": None,
                        "elapsed_time": time.time() - self.battle_start_time,
                        "source": "background_monitoring"
                    }
                    self.battle_log.append(check_event)
                    print("📊 No service on port 8081")
                    
            except Exception as e:
                # Port 80 is unreachable
                for agent_id in self.red_agents:
                    if agent_id not in self.uptime_data:
                        self.uptime_data[agent_id] = {"total_checks": 0, "successful_checks": 0}
                    self.uptime_data[agent_id]["total_checks"] += 1
                
                check_event = {
                    "timestamp": time.time(),
                    "active_agent": None,
                    "service_content": None,
                    "elapsed_time": time.time() - self.battle_start_time,
                    "source": "background_monitoring",
                    "error": str(e)
                }
                self.battle_log.append(check_event)
                self.logger.info(f"Background check: Port 8081 unreachable - {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error in monitoring check: {str(e)}")

    def _log_to_mcp_server(self):
        """Log monitoring data to MCP server."""
        try:
            if not self.battle_start_time:
                return
            
            elapsed = time.time() - self.battle_start_time
            remaining = max(0, self.battle_duration - elapsed)
            
            # Calculate current uptime percentages
            uptime_report = {}
            for agent_id, data in self.uptime_data.items():
                if data["total_checks"] > 0:
                    percentage = (data["successful_checks"] / data["total_checks"]) * 100
                    uptime_report[agent_id] = f"{percentage:.1f}%"
                else:
                    uptime_report[agent_id] = "0.0%"
            
            # Send concise log to backend
            self._send_log_to_backend(f"Monitor: {elapsed:.0f}s elapsed, {remaining:.0f}s left. Uptime: {uptime_report}")
            
        except Exception as e:
            self.logger.error(f"Error logging to MCP server: {str(e)}")

    def _judge_and_finalize_battle(self):
        """Judge the winner, generate summary, and send final result to MCP server."""
        # Determine winner
        winner, winner_percentage, rankings, summary = self._determine_final_results()
        
        # Check if this is a timeout scenario
        elapsed = time.time() - self.battle_start_time if self.battle_start_time else 0
        is_timeout = elapsed >= self.battle_duration
        
        if is_timeout and winner_percentage == 0.0:
            # All agents failed or no service was maintained
            reasoning = f"Battle timed out after {elapsed:.0f} seconds. No agent maintained service. Result: Draw."
            winner = "draw"
            self.final_judgement = {
                "winner": "draw",
                "winner_uptime": 0.0,
                "rankings": rankings,
                "summary": summary,
                "reasoning": reasoning,
                "is_timeout": True
            }
        else:
            reasoning = f"Winner is {winner} with {winner_percentage:.1f}% uptime. Rankings: {rankings}."
            self.final_judgement = {
                "winner": winner,
                "winner_uptime": winner_percentage,
                "rankings": rankings,
                "summary": summary,
                "reasoning": reasoning,
                "is_timeout": is_timeout
            }
        
        self.logger.info(f"🏁 Final Judgement: {self.final_judgement}")
        
        # Send final result to backend
        self._send_final_result_to_mcp()

    def _determine_final_results(self):
        """Helper to determine winner, rankings, and summary."""
        # Calculate uptime percentages
        uptime_report = {}
        for agent_id, data in self.uptime_data.items():
            if data["total_checks"] > 0:
                percentage = (data["successful_checks"] / data["total_checks"]) * 100
                uptime_report[agent_id] = percentage
            else:
                uptime_report[agent_id] = 0.0
        # Find the winner
        winner = max(uptime_report.items(), key=lambda x: x[1])[0] if uptime_report else None
        winner_percentage = uptime_report[winner] if winner else 0.0
        # Rankings
        rankings = sorted(uptime_report.items(), key=lambda x: x[1], reverse=True)
        # Generate summary
        elapsed = time.time() - self.battle_start_time if self.battle_start_time else 0
        summary = {
            "battle_id": self.battle_id,
            "duration": f"{elapsed:.1f} seconds",
            "total_agents": len(self.red_agents),
            "winner": winner,
            "winner_uptime": f"{winner_percentage:.1f}%",
            "all_uptime_percentages": uptime_report,
            "battle_status": "Completed"
        }
        return winner, winner_percentage, rankings, summary

    def _send_log_to_backend(self, message: str, detail: dict = None, is_result: bool = False, winner: str = None):
        """Send log or result to backend server for frontend display."""
        try:
            import requests
            from datetime import datetime
            if not self.battle_id:
                print("⚠️ No battle_id set, cannot send log to backend.")
                return
            log_data = {
                "is_result": is_result,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": message,
                "reported_by": "green_agent"
            }
            if detail:
                log_data["detail"] = detail
            if is_result and winner:
                log_data["winner"] = winner
            url = f"http://localhost:9000/battles/{self.battle_id}"
            print(f"📤 Sending log to backend: {url}")
            print(f"📤 Log data: {json.dumps(log_data, indent=2)}")
            response = requests.post(url, json=log_data, timeout=5)
            print(f"📤 Backend response: {response.status_code}")
            if response.status_code not in (200, 204):
                print(f"⚠️ Failed to send log to backend: {response.status_code} {response.text}")
            else:
                print(f"✅ Log sent successfully to backend")
        except Exception as e:
            print(f"⚠️ Error sending log to backend: {str(e)}")

    def _send_final_result_to_mcp(self):
        """Send the final result log to the MCP server with reasoning."""
        try:
            if not self.final_judgement:
                return
            final_log = {
                "reasoning": self.final_judgement["reasoning"],
                "summary": self.final_judgement["summary"]
            }
            self.logger.info(f"MCP Final Result Log: {json.dumps(self.final_judgement, indent=2)}")
            # Send to backend as result
            self._send_log_to_backend(
                message=f"Battle complete. Winner: {self.final_judgement['winner']}",
                detail=final_log,
                is_result=True,
                winner=self.final_judgement["winner"]
            )
        except Exception as e:
            self.logger.error(f"Error sending final result to MCP server: {str(e)}")

    def _create_retrieve_final_result_tool(self):
        @function_tool(name_override="get_final_battle_result")
        def get_final_battle_result() -> str:
            """
            Retrieve the final battle result, winner, and reasoning after the battle is over.
            """
            if not self.final_judgement:
                return "❌ Final result not available yet. Wait until the battle is over."
            return f"🏁 Final Judgement:\n{json.dumps(self.final_judgement, indent=2)}"
        return get_final_battle_result

    def _send_message_to_agent_auto_with_retry(self, agent_id: str, message: str, max_retries=3):
        """Send message with retry logic and better error handling"""
        for attempt in range(max_retries):
            try:
                print(f"🔍 DEBUG: Attempt {attempt + 1}/{max_retries} for {agent_id}")
                result = self._send_message_to_agent_auto(agent_id, message)
                
                # Check if result is valid
                if result and result != "None" and not str(result).startswith("Error:"):
                    print(f"✅ DEBUG: {agent_id} responded successfully on attempt {attempt + 1}")
                    return result
                else:
                    print(f"⚠️ DEBUG: {agent_id} returned invalid result on attempt {attempt + 1}: {result}")
                    
            except Exception as e:
                print(f"❌ DEBUG: Attempt {attempt + 1} failed for {agent_id}: {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < max_retries - 1:
                print(f"⏳ DEBUG: Waiting 2 seconds before retry for {agent_id}")
                time.sleep(2)
        
        print(f"❌ DEBUG: {agent_id} failed after {max_retries} attempts")
        return f"Failed after {max_retries} attempts"

    def _is_agent_ready(self, agent_url: str) -> bool:
        """Check if an agent is ready to receive messages."""
        try:
            # Simple check - just verify the agent is responding
            response = requests.get(f"{agent_url}/.well-known/agent.json", timeout=3)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ DEBUG: Agent readiness check failed for {agent_url}: {e}")
            return False

    def _create_test_message_tool(self):
        @function_tool(name_override="test_send_message_to_all_agents")
        def test_send_message_to_all_agents(message: str = "Test message from green agent") -> str:
            """
            Test function to send a message to all red agents concurrently with retry logic.
            This is for testing purposes only.
            """
            try:
                print(f"🔍 DEBUG: Starting test_send_message_to_all_agents")
                
                # Set up agent URLs manually for testing
                if not self.agent_urls or not self.red_agents:
                    print(f"🔍 DEBUG: Setting up agent URLs manually for testing")
                    self.agent_urls = {
                        "red_agent_0": "http://localhost:8001",
                        "red_agent_1": "http://localhost:8021", 
                        "red_agent_2": "http://localhost:8031"
                    }
                    self.red_agents = ["red_agent_0", "red_agent_1", "red_agent_2"]
                    print(f"🔍 DEBUG: Manual setup complete - Agent URLs: {self.agent_urls}")
                    print(f"🔍 DEBUG: Manual setup complete - Red agents: {self.red_agents}")
                
                print(f"🔍 DEBUG: Sending test message to red agents: {self.red_agents}")
                results = []
                
                # Check agent readiness first
                ready_agents = []
                for agent_id in self.red_agents:
                    agent_url = self.agent_urls.get(agent_id)
                    if agent_url:
                        ready_agents.append(agent_id)
                        print(f"✅ DEBUG: {agent_id} is ready for test message")
                    else:
                        print(f"❌ DEBUG: {agent_id} has no URL configured")
                
                if not ready_agents:
                    return "❌ No agents are ready to receive messages"
                
                # Send to all ready agents concurrently with retry logic
                import concurrent.futures
                print(f"🔍 DEBUG: Sending messages concurrently to {ready_agents}")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(ready_agents)) as executor:
                    # Submit all tasks
                    future_to_agent = {
                        executor.submit(self._send_message_to_agent_auto_with_retry, agent_id, message): agent_id 
                        for agent_id in ready_agents
                    }
                    
                    # Collect results as they complete
                    for future in concurrent.futures.as_completed(future_to_agent, timeout=45):
                        agent_id = future_to_agent[future]
                        try:
                            result = future.result()
                            print(f"🔍 DEBUG: Concurrent result for {agent_id}: {result}")
                            results.append(f"{agent_id}: {result}")
                        except concurrent.futures.TimeoutError:
                            print(f"❌ DEBUG: {agent_id} timed out in concurrent execution")
                            results.append(f"{agent_id}: Timeout in concurrent execution")
                        except Exception as e:
                            print(f"❌ DEBUG: {agent_id} failed in concurrent execution: {e}")
                            results.append(f"{agent_id}: Error in concurrent execution - {e}")
                
                print(f"🔍 DEBUG: test_send_message_to_all_agents completed")
                return f"Test message sent to all agents:\n" + "\n".join(results)
                
            except Exception as e:
                print(f"❌ DEBUG: Error in test_send_message_to_all_agents: {e}")
                import traceback
                traceback.print_exc()
                return f"❌ Error sending test messages: {e}"
        
        return test_send_message_to_all_agents

    async def invoke(self, context) -> str:
        print(context.get_user_input(), "=========================================GREEN INPUT")
        
        # Parse battle_id and agent URLs from backend notification if present
        user_input = context.get_user_input()
        try:
            import json
            battle_info = json.loads(user_input)
            if battle_info.get("type") == "battle_start" and "battle_id" in battle_info:
                self.battle_id = battle_info["battle_id"]
                print(f"🎯 Received battle_id from backend: {self.battle_id}")
                
                # Parse opponent information to get agent URLs
                if "opponent_infos" in battle_info:
                    self.agent_urls = {}
                    self.red_agents = []
                    
                    for i, opponent_info in enumerate(battle_info["opponent_infos"]):
                        agent_id = f"red_agent_{i}"
                        agent_url = opponent_info.get("agent_url")
                        
                        if agent_url:
                            self.red_agents.append(agent_id)
                            self.agent_urls[agent_id] = agent_url
                            print(f"🔗 {agent_id} -> {agent_url}")
                        else:
                            print(f"⚠️ No agent_url for opponent {opponent_info.get('name', 'unknown')}")
                    
                    print(f"📋 Parsed {len(self.red_agents)} red agents with URLs")
                
                # Send initial log to backend
                self._send_log_to_backend("Battle royale green agent initialized and ready")
        except (json.JSONDecodeError, KeyError):
            # Not a JSON battle notification, continue normally
            pass
        
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