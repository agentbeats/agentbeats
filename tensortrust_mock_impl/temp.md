我开了一个mcp服务器，让一个agent链接，但是链接的时候（agent.run()的时候会报错，你看一下为什么）

MCP定义：
# -*- coding: utf-8 -*-
from fastmcp import FastMCP

server = FastMCP("Test MCP for AgentBeast Battle Arena")

@server.tool()
def echo(message: str) -> str:
    """
    Echo the input message.
    """
    return f"Echo: {message}"


if __name__ == "__main__":
    server.run(
        transport="sse", 
        host="localhost",
        port=9123, 
        log_level="DEBUG")


Agent 运行：

import agentbeats as ab

ab_agent = ab.BeatsAgent(__name__)

@ab_agent.tool()
def helloworld_tool():
    """helloworld_tool with a docstring."""
    return "Hello from the agent tool! Your token is !@#$%^&*()"

if __name__ == "__main__":
    ab_agent.load_agent_card("ideal_agent/agent_card.toml")
    ab_agent.add_mcp_server("http://localhost:9123/sse/")
    ab_agent.run()



Agent 定义：
# -*- coding: utf-8 -*-

"""
AgentBeats SDK implementation for the AgentBeats platform.
"""

import tomllib
import asyncio
import uvicorn
from typing import Dict, List, Any, Optional

from agents import Agent, Runner
from agents.mcp import MCPServerSse
from agents import function_tool

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import TaskUpdater, InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.events import EventQueue
from a2a.utils import new_task, new_agent_text_message
from a2a.types import Part, TextPart, TaskState, AgentCard


class BeatsAgent:
    def __init__(self, name: str):
        self.name = name

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
            raise ValueError("Agent card not loaded. Please load an agent card before running.")

        # Create the application instance
        asyncio.run(self._make_app())

        # Start the server
        uvicorn.run(
            self.app,
            host=self.agent_card_json["host"],
            port=self.agent_card_json["port"],
        )

    def get_app(self) -> Optional[A2AStarletteApplication]:
        """Get the application instance for the agent."""
        return self.app
    
    async def _make_app(self) -> None:
        """Asynchronously create the application instance for the agent."""
        self.app = A2AStarletteApplication(
            agent_card=AgentCard(**self.agent_card_json),
            http_handler=DefaultRequestHandler(
                agent_executor=await AgentBeatsExecutor.create(
                    agent_card_json=self.agent_card_json,
                    mcp_url_list=self.mcp_url_list,
                    tool_list=self.tool_list,
                ),
                task_store=InMemoryTaskStore(),
            ),
        ).build()

    def tool(self, name: str = None, description: str = None):
        """Decorator to register a function as a tool for the agent."""
        def decorator(func):
            # Use function name if no name provided
            tool_name = name or func.__name__
            
            # Apply the @function_tool decorator from agents library
            # This creates the proper tool format for openai-agents
            tool_func = function_tool(name_override=tool_name)(func)
            
            # Add to the tool list
            self.tool_list.append(tool_func)
            
            return func
        return decorator


class AgentBeatsExecutor(AgentExecutor):
    def __init__(self, agent_card_json: Dict[str, Any], 
                        mcp_list: Optional[List[MCPServerSse]] = None, 
                        tool_list: Optional[List[Any]] = None):
        """ (Shouldn't be called directly) 
            Initialize the AgentBeatsExecutor with the MCP URL and agent card JSON. """
        self.agent_card_json = agent_card_json
        self.chat_history: List[Dict[str, str]] = []

        self.mcp_list = mcp_list or []
        self.tool_list = tool_list or []
        
        # construct self.AGENT_PROMPT with agent_card_json
        self.AGENT_PROMPT = str(agent_card_json["description"])
        self.AGENT_PROMPT += "\n\n"
        if "skills" in agent_card_json:
            self.AGENT_PROMPT += str(agent_card_json["skills"])

        self.main_agent = Agent(
            name=agent_card_json["name"],
            instructions=self.AGENT_PROMPT,
            model="o4-mini",
            tools=self.tool_list,
            mcp_servers=self.mcp_list,
        )

    @classmethod
    async def create(
        cls, 
        agent_card_json: Dict[str, Any],
        mcp_url_list: Optional[List[str]] = None,
        tool_list: Optional[List[Any]] = None,
    ) -> "AgentBeatsExecutor":
        """Asynchronous factory method to create a agent executor instance."""
        mcp_server_list = []
        
        if mcp_url_list:
            for mcp_url in mcp_url_list:
                try:
                    print(f"Connecting to MCP server at {mcp_url}")
                    mcp_server = MCPServerSse(
                        params={"url": mcp_url},
                        cache_tools_list=True,
                    )
                    # Try to connect to the MCP server
                    await mcp_server.connect()
                    mcp_server_list.append(mcp_server)
                except Exception as e:
                    print(f"Warning: Failed to connect to MCP server at {mcp_url}: {e}")
                    continue  # Continue without this MCP server

        instance = cls(agent_card_json, mcp_server_list, tool_list)
        return instance

    async def invoke(self, context: RequestContext) -> str:
        """Run a single turn of conversation through *self.main_agent*."""
        # Build contextual chat input for the runner
        query_ctx = self.chat_history + [{
            "content": context.get_user_input(),
            "role": "user",
        }]

        result = await Runner.run(self.main_agent, query_ctx, max_turns=30)
        self.chat_history = result.to_input_list()
        return result.final_output

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
        reply_text = await self.invoke(context)

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


运行后，MCP的后台显示：
│                                                                      │
│     🖥️  Server name:     Test MCP for AgentBeast Battle Arena         │
│     📦 Transport:       SSE                                          │
│     🔗 Server URL:      http://localhost:9123/sse/                   │
│                                                                      │
│     📚 Docs:            https://gofastmcp.com                        │
│     🚀 Deploy:          https://fastmcp.cloud                        │
│                                                                      │
│     🏎️  FastMCP version: 2.10.2                                       │
│     🤝 MCP version:     1.10.1                                       │
│                                                                      │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯




[07/14/25 12:40:49] INFO     Starting MCP server 'Test    server.py:1429
                             MCP for AgentBeast Battle                  
                             Arena' with transport 'sse'                
                             on                                         
                             http://localhost:9123/sse/                 
INFO:     Started server process [46512]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:9123 (Press CTRL+C to quit)
INFO:     ::1:6848 - "GET /sse/ HTTP/1.1" 200 OK
INFO:     ::1:6849 - "POST /messages/?session_id=b538c330908043d38ea588d20fa7a993 HTTP/1.1" 202 Accepted



Agent 报错：
(ab) PS C:\Users\24642\Desktop\agentbeats\tensortrust_mock_impl> python -m ideal_agent.main
Connecting to MCP server at http://localhost:9123/sse/
an error occurred during closing of asynchronous generator <async_generator object sse_client at 0x00000165B70039C0>
asyncgen: <async_generator object sse_client at 0x00000165B70039C0>
  + Exception Group Traceback (most recent call last):
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\anyio\_backends\_asyncio.py", line 772, in __aexit__
  |     raise BaseExceptionGroup(
  | BaseExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\mcp\client\sse.py", line 139, in sse_client
    |     yield read_stream, write_stream
    | GeneratorExit
    +------------------------------------

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\mcp\client\sse.py", line 54, in sse_client
    async with anyio.create_task_group() as tg:
               ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\anyio\_backends\_asyncio.py", line 778, in __aexit__
    if self.cancel_scope.__exit__(type(exc), exc, exc.__traceback__):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\anyio\_backends\_asyncio.py", line 457, in __exit__
    raise RuntimeError(
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
INFO:     Started server process [67288]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)


理论上而言，agent应该可以链接mcp，而不是在链接的时候报错。你应当修复这个问题。不用考虑链接错误的时候怎么try except，你只需要让他连接成功即可

此外，如果 agent 尝试调用 mcp server ，会有如下报错：

ERROR:    Exception in ASGI application
  + Exception Group Traceback (most recent call last):
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\uvicorn\protocols\http\h11_impl.py", line 403, in run_asgi
  |     result = await app(  # type: ignore[func-returns-value]
  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\uvicorn\middleware\proxy_headers.py", line 60, in __call__
  |     return await self.app(scope, receive, send)
  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\applications.py", line 112, in __call__
  |     await self.middleware_stack(scope, receive, send)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\middleware\errors.py", line 187, in __call__
  |     raise exc
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\middleware\errors.py", line 165, in __call__
  |     await self.app(scope, receive, _send)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\middleware\exceptions.py", line 62, in __call__
  |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\_exception_handler.py", line 53, in wrapped_app
  |     raise exc
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\_exception_handler.py", line 42, in wrapped_app
  |     await app(scope, receive, sender)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\routing.py", line 714, in __call__
  |     await self.middleware_stack(scope, receive, send)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\routing.py", line 734, in app
  |     await route.handle(scope, receive, send)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\routing.py", line 288, in handle
  |     await self.app(scope, receive, send)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\routing.py", line 76, in app
  |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\_exception_handler.py", line 53, in wrapped_app
  |     raise exc
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\_exception_handler.py", line 42, in wrapped_app
  |     await app(scope, receive, sender)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\starlette\routing.py", line 74, in app
  |     await response(scope, receive, send)
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\sse_starlette\sse.py", line 237, in __call__
  |     async with anyio.create_task_group() as task_group:
  |                ^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\anyio\_backends\_asyncio.py", line 772, in __aexit__
  |     raise BaseExceptionGroup(
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)   
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\sse_starlette\sse.py", line 240, in cancel_on_finish
    |     await coro()
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\sse_starlette\sse.py", line 159, in _stream_response
    |     async for data in self.body_iterator:
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\a2a\server\apps\jsonrpc\jsonrpc_app.py", line 350, in event_generator
    |     async for item in stream:
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\a2a\server\request_handlers\jsonrpc_handler.py", line 121, in on_message_send_stream
    |     async for event in self.request_handler.on_message_send_stream(
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\a2a\server\request_handlers\default_request_handler.py", line 346, in on_message_send_stream
    |     await self._cleanup_producer(producer_task, task_id)
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\a2a\utils\telemetry.py", line 161, in async_wrapper
    |     result = await func(*args, **kwargs)
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\a2a\server\request_handlers\default_request_handler.py", line 361, in _cleanup_producer
    |     await producer_task
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\a2a\utils\telemetry.py", line 161, in async_wrapper
    |     result = await func(*args, **kwargs)
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\a2a\server\request_handlers\default_request_handler.py", line 169, in _run_event_stream
    |     await self.agent_executor.execute(request, queue)
    |   File "C:\Users\24642\Desktop\agentbeats\tensortrust_mock_impl\agentbeats.py", line 176, in execute
    |     reply_text = await self.invoke(context)
    |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\Desktop\agentbeats\tensortrust_mock_impl\agentbeats.py", line 153, in invoke
    |     result = await Runner.run(self.main_agent, query_ctx, max_turns=30)
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\agents\run.py", line 200, in run
    |     return await runner.run(
    |            ^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\agents\run.py", line 359, in run
    |     all_tools = await AgentRunner._get_all_tools(current_agent, context_wrapper)
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\agents\run.py", line 1126, in _get_all_tools
    |     return await agent.get_all_tools(context_wrapper)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\agents\agent.py", line 270, in get_all_tools
    |     mcp_tools = await self.get_mcp_tools(run_context)
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\agents\agent.py", line 264, in get_mcp_tools
    |     return await MCPUtil.get_all_function_tools(
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\agents\mcp\util.py", line 109, in get_all_function_tools
    |     server_tools = await cls.get_function_tools(
    |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\agents\mcp\util.py", line 134, in get_function_tools
    |     tools = await server.list_tools(run_context, agent)
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\agents\mcp\server.py", line 248, in list_tools
    |     self._tools_list = (await self.session.list_tools()).tools    
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\mcp\client\session.py", line 386, in list_tools
    |     result = await self.send_request(
    |              ^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\mcp\shared\session.py", line 261, in send_request
    |     await self._write_stream.send(SessionMessage(message=JSONRPCMessage(jsonrpc_request), metadata=metadata))
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\anyio\streams\memory.py", line 242, in send
    |     self.send_nowait(item)
    |   File "C:\Users\24642\miniconda3\envs\ab\Lib\site-packages\anyio\streams\memory.py", line 211, in send_nowait
    |     raise ClosedResourceError
    | anyio.ClosedResourceError
    +------------------------------------
[non-fatal] Tracing client error 400: {
  "error": {
    "message": "Invalid type for 'data[1].span_data.result': expected an array of strings, but got null instead.",
    "type": "invalid_request_error",
    "param": "data[1].span_data.result",
    "code": "invalid_type"
  }
}

