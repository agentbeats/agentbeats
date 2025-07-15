# -*- coding: utf-8 -*-

import sys
import pathlib
import argparse
import importlib.util

from .agent_executor import *
from .agent_launcher import *
from . import get_registered_tools

def _import_tool_file(path: str | pathlib.Path):
    """import a Python file as a module, triggering @agentbeats.tool() decorators."""
    path = pathlib.Path(path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod        # Avoid garbage collection
    spec.loader.exec_module(mod)

def _run_agent(card_path: str, tool_files: list[str], mcp_urls: list[str]):
    # 1. Import tool files, triggering @tool decorators
    for file in tool_files:
        _import_tool_file(file)

    # 2. Instantiate agent and register tools
    agent = BeatsAgent(__name__)
    for func in get_registered_tools():
        agent.register_tool(func)       # suppose @tool() decorator adds to agent

    # 3. Load agent card / MCP, and run
    agent.load_agent_card(card_path)
    for url in mcp_urls:
        if url:                         # Allow empty string as placeholder
            agent.add_mcp_server(url)
    agent.run()

def main():
    # add support for "agentbeats run_agent ..."
    parser = argparse.ArgumentParser(prog="agentbeats")
    sub_parser = parser.add_subparsers(dest="cmd", required=True)

    # run_agent command
    run_agent_parser = sub_parser.add_parser("run_agent", help="Start an Agent from card")
    run_agent_parser.add_argument("card", help="path/to/agent_card.toml")
    run_agent_parser.add_argument("--tool", action="append", default=[],
                       help="Python file(s) that define @agentbeats.tool()")
    run_agent_parser.add_argument("--mcp",  action="append", default=[],
                       help="One or more MCP SSE server URLs")

    # run command
    run_parser = sub_parser.add_parser("run", help="Launch an Agent with controller layer")
    run_parser.add_argument("card",            help="path/to/agent_card.toml")
    run_parser.add_argument("--launcher_host", default="0.0.0.0")
    run_parser.add_argument("--launcher_port", type=int, default=8000)
    run_parser.add_argument("--backend", required=True,
                       help="Backend base URL to receive ready signal")
    run_parser.add_argument("--mcp",  action="append", default=[],
                       help="One or more MCP SSE server URLs")
    run_parser.add_argument("--tool", action="append", default=[],
                       help="Python file(s) that define @agentbeats.tool()")
    run_parser.add_argument("--reload", action="store_true")

    args = parser.parse_args()

    if args.cmd == "run_agent":
        _run_agent(args.card, args.tool, args.mcp)
    elif args.cmd == "run":
        launcher = BeatsAgentLauncher(
            agent_card=args.card,
            mcp_list=args.mcp,
            tool_list=args.tool,
            backend_url=args.backend,
            launcher_host=args.launcher_host,
            launcher_port=args.launcher_port,
        )
        launcher.run(reload=args.reload)
