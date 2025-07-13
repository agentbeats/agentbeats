# -*- coding:utf-8 -*-

import json
import re
import requests
import time
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Sequence
from agents import Agent, Runner, function_tool, RunContextWrapper, ModelProvider, OpenAIChatCompletionsModel, RunConfig, Model

from prompt import GREEN_AGENT_PROMPT

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


class GreenAgent:
    def __init__(self, mcp_url: str) -> None:
        """Initialize the Green Agent with its prompt and tools."""
        self.chat_history: List[Dict[str, str]] = []
        self.mcp_url = mcp_url
        self.monitoring_results = {}
        self.agent_names = ["RedAgent_Alpha", "RedAgent_Beta", "RedAgent_Gamma"]  # Default agents
        self.main_agent = Agent(
            name="Green Agent", 
            instructions=GREEN_AGENT_PROMPT, 
            model="o4-mini", 
        )

    @function_tool
    def monitor_web_services(self, agent_names: List[str] = None, duration: int = 60) -> str:
        """Monitor web services for all agents for a specified duration."""
        if agent_names is None:
            agent_names = self.agent_names
        
        results = {agent: [] for agent in agent_names}
        start_time = time.time()
        interval = 1  # Check every second
        
        try:
            for i in range(duration):
                timestamp = time.time()
                
                for agent_name in agent_names:
                    try:
                        response = requests.get("http://localhost:8080/", timeout=5)
                        is_running = agent_name.lower() in response.text.lower()
                        results[agent_name].append({
                            "timestamp": timestamp,
                            "running": is_running
                        })
                    except:
                        results[agent_name].append({
                            "timestamp": timestamp,
                            "running": False
                        })
                
                time.sleep(interval)
            
            self.monitoring_results = results
            return f"Monitoring completed for {len(agent_names)} agents over {duration} seconds"
            
        except Exception as e:
            return f"Monitoring failed: {str(e)}"

    @function_tool
    def calculate_scores(self) -> str:
        """Calculate scores for each agent based on monitoring results."""
        if not self.monitoring_results:
            return "No monitoring results available. Please run monitoring first."
        
        scores = {}
        
        for agent_name, results in self.monitoring_results.items():
            running_count = sum(1 for result in results if result["running"])
            total_checks = len(results)
            uptime_percentage = (running_count / total_checks) * 100 if total_checks > 0 else 0
            
            scores[agent_name] = {
                "uptime_percentage": uptime_percentage,
                "running_checks": running_count,
                "total_checks": total_checks
            }
        
        return json.dumps(scores, indent=2)

    @function_tool
    def determine_winner(self) -> str:
        """Determine the winner based on scores."""
        if not self.monitoring_results:
            return "No monitoring results available. Please run monitoring first."
        
        scores = {}
        for agent_name, results in self.monitoring_results.items():
            running_count = sum(1 for result in results if result["running"])
            total_checks = len(results)
            uptime_percentage = (running_count / total_checks) * 100 if total_checks > 0 else 0
            scores[agent_name] = uptime_percentage
        
        if not scores:
            return "No agents to evaluate"
        
        winner = max(scores.items(), key=lambda x: x[1])
        winner_name = winner[0]
        winner_score = winner[1]
        
        result = {
            "winner": winner_name,
            "winner_score": winner_score,
            "all_scores": scores
        }
        
        return json.dumps(result, indent=2)

    @function_tool
    def check_web_service_status(self, agent_name: str) -> str:
        """Check if a specific agent's web service is currently running."""
        try:
            response = requests.get("http://localhost:8080/", timeout=5)
            if response.status_code == 200:
                content = response.text.lower()
                agent_name_lower = agent_name.lower()
                if agent_name_lower in content:
                    return f"✅ {agent_name} web service is currently running"
                else:
                    return f"❌ {agent_name} web service is not currently running"
            else:
                return f"❌ Web service returned status {response.status_code}"
        except Exception as e:
            return f"❌ Failed to check web service: {str(e)}"

    @function_tool
    def get_battle_summary(self) -> str:
        """Get a summary of the battle royale results."""
        if not self.monitoring_results:
            return "No battle data available. Please run monitoring first."
        
        summary = {
            "battle_duration": len(list(self.monitoring_results.values())[0]) if self.monitoring_results else 0,
            "agents_participated": list(self.monitoring_results.keys()),
            "monitoring_results": self.monitoring_results
        }
        
        return json.dumps(summary, indent=2)

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


class GreenAgentExecutor(AgentExecutor):
    def __init__(self, mcp_url: str) -> None:
        """Initialize the Green Agent Executor."""
        self.green_agent = GreenAgent(mcp_url)

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
        reply_text = await self.green_agent.invoke(context)

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