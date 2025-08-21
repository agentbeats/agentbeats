# -*- coding: utf-8 -*-

"""
AgentBeats SDK implementation for the AgentBeats platform.
"""

import os
import json
import tomllib
import uvicorn
import functools
from typing import *
import inspect
import logging

logger = logging.getLogger(__name__)


from agents import (
    Agent,
    Runner,
    function_tool,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    RunHooks,
)
from agents.mcp import MCPServerSse
from openai import AsyncOpenAI

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import TaskUpdater, InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.events import EventQueue
from a2a.utils import new_task, new_agent_text_message
from a2a.types import Part, TextPart, TaskState, AgentCard

from .logging import (
    update_battle_process,
    set_battle_context,
    get_battle_context,
    get_battle_id,
    get_agent_id,
    get_frontend_agent_name,
    get_backend_url,
)

# class AgentBeatsHook(RunHooks):
#     """Custom hooks for AgentBeats to handle agent execution events."""
#     def __init__(self, battle_context: Dict[str, Any]):
#         super().__init__()
#         self.battle_context = battle_context

#     def on_tool_start(self, context, agent, tool):
#         update_battle_process(
#             battle_id=self.battle_context["battle_id"],
#             backend_url=self.battle_context["backend_url"],
#             message=f"Agent {agent.name} finished using tool {tool.name}.",
#             # detail=tool.params_json_schema,
#             reported_by=agent.name + " (from agentbeats sdk toolcall hooks)"
#         )
#         return super().on_tool_start(context, agent, tool)

__all__ = [
    "BeatsAgent",
    "AgentBeatsExecutor",
]


def create_agent(
    agent_name: str,
    instructions: str,
    model_type: str,
    model_name: str,
    tools: Optional[List[Any]] = None,
    mcp_servers: Optional[List[MCPServerSse]] = None,
) -> Agent:
    """Create an Agent instance based on the model type and name."""

    agent_args = {
        "name": agent_name,
        "instructions": instructions,
        "tools": tools or [],
        "mcp_servers": mcp_servers or [],
    }

    # openai agents, e.g. "o4-mini"
    if model_type == "openai":
        OPENAI_API_KEY = os.getenv(
            "OPENAI_API_KEY"
        ).strip()  # in case of empty \n
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")

        print("[AgentBeats] Using OpenAI model:", model_name)
        return Agent(**agent_args, model=model_name)

    # openrouter agents, e.g. "anthropic/claude-3.5-sonnet"
    elif model_type == "openrouter":
        OPENROUTER_API_KEY = os.getenv(
            "OPENROUTER_API_KEY"
        ).strip()  # in case of empty \n
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not set")

        print("[AgentBeats] Using OpenRouter model:", model_name)
        set_tracing_disabled(True)  # Disable tracing for OpenRouter models
        os.environ["OPENAI_TRACING_V2"] = "false"
        openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY
        )
        openrouter_model_provider = OpenRouterModelProvider()
        return Agent(
            **agent_args,
            model=openrouter_model_provider.get_model(
                model_name, openrouter_client
            ),
        )

    # no matching agents
    else:
        raise ValueError(f"Unsupported model type: {model_type}.")


class OpenRouterModelProvider(ModelProvider):
    """Provider for OpenRouter models, allowing dynamic model in openai-agents."""

    def get_model(
        self, model_name: str, openrouter_client: AsyncOpenAI
    ) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name, openai_client=openrouter_client
        )


class BeatsAgent:
    def __init__(
        self,
        name: str,
        agent_host: str,
        agent_port: int,
        model_type: str,
        model_name: str,
    ):
        self.name = name
        self.agent_host = agent_host
        self.agent_port = agent_port
        self.model_type = model_type
        self.model_name = model_name

        self.tool_list: List[Any] = []
        self.mcp_url_list: List[str] = []
        self.agent_card_json = None
        self.app = None

    def load_agent_card(self, card_path: str):
        """Load agent card from a TOML file."""
        with open(card_path, "rb") as f:
            self.agent_card_json = tomllib.load(f)

    def add_mcp_server(self, url: str):
        """Add a MCP server to the agent."""
        self.mcp_url_list.append(url)

    def run(self):
        """Run the agent."""

        # Ensure the agent card is loaded before running
        if not self.agent_card_json:
            raise ValueError(
                "Agent card not loaded. Please load an agent card before running."
            )

        # Create the application instance
        self._make_app()

        # Start the server
        uvicorn.run(
            self.app,
            host=self.agent_host,
            port=self.agent_port,
        )

    def get_app(self) -> Optional[A2AStarletteApplication]:
        """Get the application instance for the agent."""
        return self.app

    def _make_app(self) -> None:
        """Asynchronously create the application instance for the agent."""
        self.app = A2AStarletteApplication(
            agent_card=AgentCard(**self.agent_card_json),
            http_handler=DefaultRequestHandler(
                agent_executor=AgentBeatsExecutor(
                    agent_card_json=self.agent_card_json,
                    model_type=self.model_type,
                    model_name=self.model_name,
                    mcp_url_list=self.mcp_url_list,
                    tool_list=self.tool_list,
                ),
                task_store=InMemoryTaskStore(),
            ),
        ).build()

    def _register_tool(self, func: Callable, name: str | None = None):
        """Register a tool function with the agent."""
        self.tool_list.append(func)
        return func

    def tool(self, func: Callable | None = None, *, name: str | None = None):
        """
        Usage 1: @agent.tool                -> No-argument decorator
        Usage 2: @agent.tool(name="Search") -> Argument decorator with name
        Usage 3: agent.tool(func_obj)       -> Directly register a function
        """
        if func is None:
            # @agent.tool(name="xxx"), a decorator with name argument
            def decorator(f):
                self._register_tool(f, name=name)
                return f  # Keep the original function usable

            return decorator
        else:
            # Supports both @agent.tool as a no-argument decorator and explicit call agent.tool(foo)
            return self._register_tool(func, name=name)

    register_tool = tool  # Alias for backward compatibility


class AgentBeatsExecutor(AgentExecutor):
    def __init__(
        self,
        agent_card_json: Dict[str, Any],
        model_type: str,
        model_name: str,
        mcp_url_list: Optional[List[str]] = None,
        tool_list: Optional[List[Any]] = None,
    ):
        """(Shouldn't be called directly)
        Initialize the AgentBeatsExecutor with the MCP URL and agent card JSON.
        """
        self.agent_card_json = agent_card_json
        self.model_type = model_type
        self.model_name = model_name
        self.chat_history: List[Dict[str, str]] = []

        self.mcp_url_list = mcp_url_list or []
        self.mcp_list = [
            MCPServerSse(
                client_session_timeout_seconds=20,
                cache_tools_list=True,
                params={"url": url, "timeout": 5, "sse_read_timeout": 20},
            )
            for url in self.mcp_url_list
        ]
        self.tool_list = tool_list or []

        # construct self.AGENT_PROMPT with agent_card_json
        self.AGENT_PROMPT = str(agent_card_json["description"])
        self.AGENT_PROMPT += "\n\n"
        if "skills" in agent_card_json:
            self.AGENT_PROMPT += (
                "Here are your skills defined in your agent card:\n"
            )
            self.AGENT_PROMPT += json.dumps(
                agent_card_json["skills"], indent=2
            )
            self.AGENT_PROMPT += "\n\n"
            self.AGENT_PROMPT += (
                "You should use these skills to help the user.\n"
            )
        self.AGENT_PROMPT += "Above is your system prompt. Please respond accordingly. The below will be your user input: \n"

        self.main_agent = None

    def _wrap_tool_with_logging(self, tool_fn):
        """
        Wrap tool_fn with logging:
        - Extract battle_id and backend_url from battle_context
        - Log function parameters only once before calling
        - Return the result of tool_fn
        """

        def log(params_json: dict):
            if not get_battle_context():  # if no battle context, skip logging
                return
            try:
                update_battle_process(
                    battle_id=get_battle_id(),
                    backend_url=get_backend_url(),
                    message=f"Calling tool {tool_fn.__name__}",
                    detail=params_json,
                    reported_by=(
                        get_frontend_agent_name()
                        + " (agentbeats sdk toolcall hooks)"
                    ),
                )
            except Exception:
                pass

        if inspect.iscoroutinefunction(tool_fn):

            @functools.wraps(tool_fn)
            async def async_wrapper(*args, **kwargs):
                sig = inspect.signature(tool_fn)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                # bound.arguments is an OrderedDict of param_name -> value
                json_body = json.loads(
                    json.dumps(bound.arguments, default=str)
                )
                log(json_body)
                return await tool_fn(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(tool_fn)
            def sync_wrapper(*args, **kwargs):
                sig = inspect.signature(tool_fn)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                arguments_dict = json.loads(
                    json.dumps(bound.arguments, default=str)
                )

                if "terminal_command" in arguments_dict:
                    result = tool_fn(*args, **kwargs)
                    # NOTE: (@lukeleeai) with this implementation, we should enforce the users to use the following args and return keys
                    # TODO: perhaps make it more flexible later?
                    terminal_input = arguments_dict["terminal_command"]
                    terminal_output = result["terminal_output"]
                    if "asciinema_url" in result:
                        asciinema_url = result["asciinema_url"]
                    else:
                        asciinema_url = None

                    logger.info("Arguments dict: %s", arguments_dict)
                    logger.info("Terminal input: %s", terminal_input)
                    logger.info("Terminal output: %s", terminal_output)
                    logger.info("Asciinema url: %s", asciinema_url)

                    # log the asciinema to the battle process
                    try:
                        update_battle_process(
                            battle_id=get_battle_id(),
                            backend_url=get_backend_url(),
                            message=f"Showing terminal...",
                            terminal_input=terminal_input,
                            terminal_output=terminal_output,
                            asciinema_url=asciinema_url,
                            reported_by=(
                                get_frontend_agent_name()
                                + " (agentbeats sdk toolcall hooks)"
                            ),
                        )
                        return result
                    except Exception as e:
                        logger.error(
                            "[agent_executor] Error when recording to backend for battle %s: %s",
                            get_battle_id(),
                            str(e),
                        )
                else:
                    log(arguments_dict)
                    result = tool_fn(*args, **kwargs)
                return result

            return sync_wrapper

    async def _init_agent_and_mcp(self):
        """Initialize the main agent with the provided tools and MCP servers."""

        # Register tools
        for tool_index in range(len(self.tool_list)):
            tool = self.tool_list[tool_index]
            tool_name = tool.__name__
            logged_tool = self._wrap_tool_with_logging(tool)
            wrapped = function_tool(name_override=tool_name)(logged_tool)
            self.tool_list[tool_index] = wrapped

        # Connect to all MCP servers
        for mcp_server in self.mcp_list:
            await mcp_server.connect()

        # Create the main agent with the provided tools and MCP servers
        self.main_agent = create_agent(
            agent_name=self.agent_card_json["name"],
            model_type=self.model_type,
            model_name=self.model_name,
            instructions=self.AGENT_PROMPT,
            tools=self.tool_list,
            mcp_servers=self.mcp_list,
        )

        # Print agent instructions for debugging
        print(
            f"[AgentBeatsExecutor] Initializing agent: {self.main_agent.name} with {len(self.tool_list)} tools and {len(self.mcp_list)} MCP servers."
        )
        print(f"[AgentBeatsExecutor] Agent instructions: {self.AGENT_PROMPT}")

    async def invoke_agent(self, context: RequestContext) -> str:
        """Run a single turn of conversation through *self.main_agent*."""
        # Init agent and MCP servers if not already done
        # Must initialize here, because agent init and server run (mcp serve) must be in the same asyncio loop
        if not self.main_agent:
            await self._init_agent_and_mcp()

        # print agent input
        print(f"[AgentBeatsExecutor] Agent input: {context.get_user_input()}")

        # Build contextual chat input for the runner
        query_ctx = self.chat_history + [
            {
                "content": context.get_user_input(),
                "role": "user",
            }
        ]

        result = await Runner.run(self.main_agent, query_ctx, max_turns=30)
        self.chat_history = result.to_input_list()
        # print(self.chat_history)

        # print agent output
        print(f"[AgentBeatsExecutor] Agent output: {result.final_output}")

        return result.final_output

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the agent with the given context and event queue."""

        # make / get current task first
        task = context.current_task
        if task is None:  # first chat
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        # push "working now" status
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("", task.context_id, task.id),
        )

        # try to parse battle_info from the request
        try:
            raw_input_str = context.get_user_input()
            raw_input_json = json.loads(raw_input_str)

            set_battle_context(
                {
                    "frontend_agent_name": raw_input_json["agent_name"],
                    "agent_id": raw_input_json["agent_id"],
                    "battle_id": raw_input_json["battle_id"],
                    "backend_url": raw_input_json["backend_url"],
                }
            )
            # self.battle_context_hook = AgentBeatsHook(self.battle_context)
            print(
                "[AgentBeatsExecutor] Battle context parsed:",
                get_battle_context(),
            )

            reply_text = (
                f"Agent {get_frontend_agent_name()} is ready to battle!"
            )

        # if battle_info is not provided (normal conversation),
        # use the agent output as the reply text
        except Exception:
            reply_text = await self.invoke_agent(context)

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

    async def cleanup(self) -> None:
        """Clean up MCP connections."""
        if self.mcp_list:
            for mcp_server in self.mcp_list:
                try:
                    await mcp_server.close()
                except Exception as e:
                    print(f"Warning: Error closing MCP server: {e}")
