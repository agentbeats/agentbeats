# -*- coding: utf-8 -*-

import sys
import pathlib
import argparse
import importlib.util
import subprocess
import threading
import time
import signal
import atexit
import uvicorn
import os

from .agent_executor import *
from .agent_launcher import *
from .utils.deploy.scenario_manager import ScenarioManager
from . import get_registered_tools, tool
from .utils.deploy.deploy import _deploy_current_terminal, _deploy_separate_terminals, _deploy_tmux


def _check_environment():
    """Check AgentBeats environment setup"""
    
    print("Checking AgentBeats Environment Setup...")
    print("=" * 50)
    
    # Find directories
    current_dir = pathlib.Path(__file__).parent.parent.parent  # Go up to project root
    backend_dir = current_dir / "src" / "agentbeats_backend"
    frontend_dir = current_dir / "frontend" / "webapp"
    
    issues = []
    warnings = []
    
    # 1. Check backend files
    print("[1/5] Checking backend files...")
    backend_app = backend_dir / "app.py"
    mcp_server = backend_dir / "mcp" / "mcp_server.py"
    
    if backend_app.exists():
        print("  ✓ Backend app.py found")
    else:
        print("  ✗ Backend app.py NOT found")
        issues.append("Backend app.py missing")
    
    if mcp_server.exists():
        print("  ✓ MCP server found")
    else:
        print("  ✗ MCP server NOT found")
        issues.append("MCP server missing")
    
    # 2. Check frontend files
    print("\n[2/5] Checking frontend files...")
    frontend_package_json = frontend_dir / "package.json"
    frontend_node_modules = frontend_dir / "node_modules"
    
    if frontend_package_json.exists():
        print("  ✓ Frontend package.json found")
    else:
        print("  ✗ Frontend package.json NOT found")
        issues.append("Frontend package.json missing")
    
    if frontend_node_modules.exists():
        print("  ✓ Frontend dependencies installed")
    else:
        print("  ✗ Frontend dependencies NOT installed")
        issues.append("Frontend dependencies not installed (run: agentbeats run_frontend --mode install)")
    
    # 3. Check root .env file
    print("\n[3/5] Checking root .env file...")
    root_env = current_dir / ".env"
    
    if root_env.exists():
        print("  ✓ Root .env file found")
        try:
            with open(root_env, 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            if "SUPABASE_URL" in env_content:
                print("  ✓ SUPABASE_URL found in root .env")
            else:
                print("  ✗ SUPABASE_URL NOT found in root .env")
                issues.append("SUPABASE_URL missing in root .env")
            
            if "SUPABASE_ANON_KEY" in env_content:
                print("  ✓ SUPABASE_ANON_KEY found in root .env")
            else:
                print("  ✗ SUPABASE_ANON_KEY NOT found in root .env")
                issues.append("SUPABASE_ANON_KEY missing in root .env")
        except Exception as e:
            print(f"  ⚠ Error reading root .env: {e}")
            warnings.append(f"Could not read root .env: {e}")
    else:
        print("  ✗ Root .env file NOT found")
        issues.append("Root .env file missing")
    
    # 4. Check frontend .env file
    print("\n[4/5] Checking frontend .env file...")
    frontend_env = frontend_dir / ".env"
    
    if frontend_env.exists():
        print("  ✓ Frontend .env file found")
        try:
            with open(frontend_env, 'r', encoding='utf-8') as f:
                frontend_env_content = f.read()
            
            if "VITE_SUPABASE_URL" in frontend_env_content:
                print("  ✓ VITE_SUPABASE_URL found in frontend .env")
            else:
                print("  ✗ VITE_SUPABASE_URL NOT found in frontend .env")
                issues.append("VITE_SUPABASE_URL missing in frontend .env")
            
            if "VITE_SUPABASE_ANON_KEY" in frontend_env_content:
                print("  ✓ VITE_SUPABASE_ANON_KEY found in frontend .env")
            else:
                print("  ✗ VITE_SUPABASE_ANON_KEY NOT found in frontend .env")
                issues.append("VITE_SUPABASE_ANON_KEY missing in frontend .env")
        except Exception as e:
            print(f"  ⚠ Error reading frontend .env: {e}")
            warnings.append(f"Could not read frontend .env: {e}")
    else:
        print("  ✗ Frontend .env file NOT found")
        issues.append("Frontend .env file missing")
    
    # 5. Check system environment variables
    print("\n[5/5] Checking system environment variables...")
    
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        print("  ✓ OPENAI_API_KEY found in system environment")
    else:
        print("  ✗ OPENAI_API_KEY NOT found in system environment")
        warnings.append("OPENAI_API_KEY missing (needed for OpenAI models)")
    
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        print("  ✓ OPENROUTER_API_KEY found in system environment")
    else:
        print("  ✗ OPENROUTER_API_KEY NOT found in system environment")
        warnings.append("OPENROUTER_API_KEY missing (needed for OpenRouter models)")
    
    # Summary
    print("\n" + "=" * 50)
    print("Environment Check Summary:")
    print("=" * 50)
    
    if not issues and not warnings:
        print("🎉 All checks passed! Your environment is ready.")
    else:
        if issues:
            print(f"❌ {len(issues)} critical issue(s) found:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} warning(s):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
    
    if issues or warnings:
        print("\n" + "=" * 50)
        print("Fix Suggestions:")
        print("Refer to the AgentBeats documentation for setup instructions")
    
    print("\n" + "=" * 50)
    return len(issues) == 0

def _run_deploy(mode: str, backend_port: int, frontend_port: int, mcp_port: int, launch_mode: str):
    """Deploy AgentBeats with backend, frontend, and MCP server"""
    
    print(f"Deploying AgentBeats in {mode} mode with {launch_mode} launch...")
    print("=" * 50)
    if backend_port != 9000 or mcp_port != 9001:
        print(f"Warning: Backend port is set to {backend_port}, MCP port is set to {mcp_port}.")
        print("Make sure your [mcp, frontend, agents] are configured to connect to these ports.")
    
    # Find directories
    current_dir = pathlib.Path(__file__).parent.parent.parent  # Go up to project root
    mcp_server_path = current_dir / "src" / "agentbeats_backend" / "mcp" / "mcp_server.py"
    
    if not mcp_server_path.exists():
        print(f"Error: MCP server not found at {mcp_server_path}")
        sys.exit(1)
    
    # Route to different launch methods
    if launch_mode == "separate":
        _deploy_separate_terminals(mode, backend_port, frontend_port, mcp_port, current_dir, mcp_server_path)
    elif launch_mode == "tmux":
        _deploy_tmux(mode, backend_port, frontend_port, mcp_port, current_dir, mcp_server_path)
    else:  # current
        _deploy_current_terminal(mode, backend_port, frontend_port, mcp_port, current_dir, mcp_server_path)


def _run_frontend(mode: str, host: str, port: int):
    """Start the AgentBeats frontend server"""
    import subprocess
    import os
    import pathlib
    
    # Find the frontend directory
    current_dir = pathlib.Path(__file__).parent.parent.parent  # Go up to project root
    frontend_dir = current_dir / "frontend" / "webapp"
    
    if not frontend_dir.exists():
        print(f"Error: Frontend directory not found at {frontend_dir}")
        print("Make sure you're running this from the AgentBeats project root.")
        sys.exit(1)

    if mode == "install":
        print("Installing frontend dependencies...")
        try:
            subprocess.run("npm install", cwd=frontend_dir, check=True, shell=True)
            print("Frontend dependencies installed successfully!")
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"Error installing frontend dependencies: {e}")
            sys.exit(1)

    # Check if frontend installed
    if not (frontend_dir / "node_modules").exists():
        print(f"Error: Frontend dependencies not installed. Run `agentbeats run_frontend --mode install` to install them.")
        sys.exit(1)
    
    print(f"Starting AgentBeats Frontend in {mode} mode...")
    print(f"Frontend directory: {frontend_dir}")
    print("Note: Assume backend is running at http://localhost:9000, if not, please go to `frontend/webapp/vite.config.js` to change the backend URL.")
    
    try:
        if mode == "dev":
            print(f"Development server will be available at http://{host}:{port}")
            print("Press Ctrl+C to stop the server")
            # Run development server
            subprocess.run(
                f"npm run dev -- --host {host} --port {str(port)}", 
                cwd=frontend_dir, check=True, shell=True
            )
            
        elif mode == "build":
            print("Building frontend for production...")
            # Build for production
            subprocess.run("npm run build", cwd=frontend_dir, check=True, shell=True)
            print("Build completed successfully!")
            print(f"Built files are in {frontend_dir / 'build'}")
            
        elif mode == "preview":
            print("Building and previewing production build...")
            # First build
            subprocess.run("npm run build", cwd=frontend_dir, check=True, shell=True)
            # Then preview
            print(f"Preview server will be available at http://{host}:{port}")
            print("Press Ctrl+C to stop the server")
            subprocess.run(
                f"npm run preview -- --host {host} --port {str(port)}", 
                cwd=frontend_dir, check=True, shell=True
            )
            
    except subprocess.CalledProcessError as e:
        print(f"Error running frontend command: {e}")
        print("Make sure Node.js and npm are installed and frontend dependencies are installed.")
        print(f"Try running: cd {frontend_dir} && npm install")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: npm command not found.")
        print("Make sure Node.js and npm are installed.")
        sys.exit(1)


def _run_backend(host: str, port: int, reload: bool = False):
    """Start the AgentBeats backend server"""
    if port != 9000:
        print(f"Warning: Backend port is set to {port}, which is not the default 9000. Make sure your [frontend, mcp, agents] are configured to connect to this port.")
    try:
        print(f"Starting AgentBeats Backend...")
        print(f"API will be available at http://{host}:{port}")
        print("Press Ctrl+C to stop the server")
        
        # Use the module name for uvicorn to properly handle imports
        uvicorn.run(
            "agentbeats_backend.app:app",
            host=host,
            port=port,
            reload=reload
        )
    except Exception as e:
        print(f"Error starting backend: {e}")
        print("Make sure all backend dependencies are installed.")
        sys.exit(1)


def _import_tool_file(path: str | pathlib.Path):
    """import a Python file as a module, triggering @agentbeats.tool() decorators."""
    path = pathlib.Path(path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None:
        raise ImportError(f"Could not create spec for {path}")
    
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod        # Avoid garbage collection
    if spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    
    spec.loader.exec_module(mod)

def _run_agent(card_path: str, 
               agent_host: str,
               agent_port: int,
               model_type: str,
               model_name: str,
               tool_files: list[str], 
               mcp_urls: list[str], 
               ):
    # 1. Import tool files, triggering @tool decorators
    for file in tool_files:
        _import_tool_file(file)

    # 2. Instantiate agent and register tools
    agent = BeatsAgent(__name__, 
                       agent_host=agent_host, 
                       agent_port=agent_port, 
                       model_type=model_type,
                       model_name=model_name,)
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
    run_agent_parser.add_argument("--agent_host", default="0.0.0.0")
    run_agent_parser.add_argument("--agent_port", type=int, default=8001)
    run_agent_parser.add_argument("--model_type", default="openai", 
                       help="Model type to use, e.g. 'openai', 'openrouter', etc.")
    run_agent_parser.add_argument("--model_name", default="o4-mini",
                       help="Model name to use, e.g. 'o4-mini', etc.")
    run_agent_parser.add_argument("--tool", action="append", default=[],
                       help="Python file(s) that define @agentbeats.tool()")
    run_agent_parser.add_argument("--mcp",  action="append", default=[],
                       help="One or more MCP SSE server URLs")

    # run command
    run_parser = sub_parser.add_parser("run", help="Launch an Agent with controller layer")
    run_parser.add_argument("card",            help="path/to/agent_card.toml")
    run_parser.add_argument("--agent_host", default="0.0.0.0")
    run_parser.add_argument("--agent_port", type=int, default=8001)
    run_parser.add_argument("--launcher_host", default="0.0.0.0")
    run_parser.add_argument("--launcher_port", type=int, default=8000)
    run_parser.add_argument("--model_type", default="openai", 
                       help="Model type to use, e.g. 'openai', 'openrouter', etc.")
    run_parser.add_argument("--model_name", default="o4-mini",
                       help="Model name to use, e.g. 'o4-mini', etc.")
    run_parser.add_argument("--mcp",  action="append", default=[],
                       help="One or more MCP SSE server URLs")
    run_parser.add_argument("--tool", action="append", default=[],
                       help="Python file(s) that define @agentbeats.tool()")
    run_parser.add_argument("--reload", action="store_true")

    # load_scenario command
    load_scenario_parser = sub_parser.add_parser("load_scenario", help="Launch a complete scenario from scenario.toml")
    load_scenario_parser.add_argument("scenario_name", help="Name of the scenario folder")
    load_scenario_parser.add_argument("--launch-mode", choices=["tmux", "separate", "current"], 
                                default="", help="Launch mode (default: tmux)")
    load_scenario_parser.add_argument("--scenarios-root", help="Path to scenarios directory")
    load_scenario_parser.add_argument("--backend", help="Override backend URL for all agents")

    # run_scenario command
    run_scenario_parser = sub_parser.add_parser("run_scenario", help="Run a scenario from scenario.toml")
    run_scenario_parser.add_argument("scenario_name", help="Name of the scenario folder")
    run_scenario_parser.add_argument("--launch-mode", choices=["tmux", "separate", "current"],
                                default="", help="Launch mode (default: tmux)")
    run_scenario_parser.add_argument("--scenarios-root", help="Path to scenarios directory")
    run_scenario_parser.add_argument("--backend", help="Backend URL", default="http://localhost:9000")
    run_scenario_parser.add_argument("--frontend", help="Frontend URL", default="http://localhost:5173")

    # run_backend command
    backend_parser = sub_parser.add_parser("run_backend", help="Start the AgentBeats backend server")
    backend_parser.add_argument("--host", default="0.0.0.0", help="Backend host (default: 0.0.0.0)")
    backend_parser.add_argument("--port", type=int, default=9000, help="Backend port (default: 9000)")
    backend_parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    # run_frontend command
    frontend_parser = sub_parser.add_parser("run_frontend", help="Start the AgentBeats frontend server")
    frontend_parser.add_argument("--mode", choices=["dev", "build", "preview", "install"], default="dev", 
                                help="Frontend mode: dev (development), build (production build), preview (build + preview), install (install dependencies)")
    frontend_parser.add_argument("--host", default="localhost", help="Frontend host (default: localhost)")
    frontend_parser.add_argument("--port", type=int, default=5173, help="Frontend port (default: 5173)")

    # deploy command
    deploy_parser = sub_parser.add_parser("deploy", help="Deploy complete AgentBeats stack (backend + frontend + MCP)")
    deploy_parser.add_argument("--mode", choices=["dev", "build"], default="dev",
                              help="Deployment mode: dev (development) or build (production)")
    deploy_parser.add_argument("--launch-mode", choices=["current", "separate", "tmux"], default="current",
                              help="Launch mode: current (same terminal), separate (separate terminals), tmux (tmux session)")
    deploy_parser.add_argument("--backend-port", type=int, default=9000, help="Backend port (default: 9000)")
    deploy_parser.add_argument("--frontend-port", type=int, default=5173, help="Frontend port (default: 5173)")
    deploy_parser.add_argument("--mcp-port", type=int, default=9001, help="MCP server port (default: 9001)")

    # check command
    check_parser = sub_parser.add_parser("check", help="Check AgentBeats environment setup")

    args = parser.parse_args()

    if args.cmd == "run_agent":
        _run_agent(card_path=args.card, 
                   agent_host=args.agent_host,
                   agent_port=args.agent_port,
                   model_name=args.model_name,
                   model_type=args.model_type,
                   tool_files=args.tool, 
                   mcp_urls=args.mcp)
    elif args.cmd == "run":
        launcher = BeatsAgentLauncher(
            agent_card=args.card,
            launcher_host=args.launcher_host,
            launcher_port=args.launcher_port,
            agent_host=args.agent_host,
            agent_port=args.agent_port,
            model_type=args.model_type,
            model_name=args.model_name,
            mcp_list=args.mcp,
            tool_list=args.tool,
        )
        launcher.run(reload=args.reload)
    elif args.cmd == "load_scenario":
        scenarios_root = pathlib.Path(args.scenarios_root) if args.scenarios_root else None
        manager = ScenarioManager(scenarios_root)
        manager.load_scenario(args.scenario_name, args.launch_mode, backend_override=args.backend)
    elif args.cmd == "run_scenario":
        scenarios_root = pathlib.Path(args.scenarios_root) if args.scenarios_root else None
        manager = ScenarioManager(scenarios_root)
        manager.load_scenario(args.scenario_name, args.launch_mode, backend_override=args.backend)
        time.sleep(10)
        manager.start_battle(args.scenario_name, args.backend, args.frontend)
    elif args.cmd == "run_backend":
        _run_backend(host=args.host, port=args.port, reload=args.reload)
    elif args.cmd == "run_frontend":
        _run_frontend(mode=args.mode, host=args.host, port=args.port)
    elif args.cmd == "deploy":
        _run_deploy(mode=args.mode, backend_port=args.backend_port, 
                   frontend_port=args.frontend_port, mcp_port=args.mcp_port, 
                   launch_mode=args.launch_mode)
    elif args.cmd == "check":
        _check_environment()
