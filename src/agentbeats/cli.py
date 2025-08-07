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
    backend_dir = current_dir / "src" / "backend"
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
        issues.append("Frontend dependencies not installed (run: agentbeats install_frontend)")
    
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

def _run_deploy(deploy_mode: str, backend_port: int, frontend_port: int, mcp_port: int, launch_mode: str, supabase_auth: bool, public_url: str = None):
    """Deploy AgentBeats with backend, frontend, and MCP server"""
    
    print(f"Deploying AgentBeats in {deploy_mode} mode with {launch_mode} launch...")
    print("=" * 50)
    
    # Find directories
    current_dir = pathlib.Path(__file__).parent.parent.parent  # Go up to project root
    mcp_server_path = current_dir / "src" / "backend" / "mcp" / "mcp_server.py"
    
    if not mcp_server_path.exists():
        print(f"Error: MCP server not found at {mcp_server_path}")
        sys.exit(1)
    
    # Route to different launch methods
    if launch_mode == "separate":
        _deploy_separate_terminals(deploy_mode, backend_port, frontend_port, mcp_port, current_dir, mcp_server_path, supabase_auth, public_url)
    elif launch_mode == "tmux":
        _deploy_tmux(deploy_mode, backend_port, frontend_port, mcp_port, current_dir, mcp_server_path, supabase_auth, public_url)
    else:  # current
        _deploy_current_terminal(deploy_mode, backend_port, frontend_port, mcp_port, current_dir, mcp_server_path, supabase_auth, public_url)


def _run_frontend(frontend_mode: str, host: str, port: int, webapp_version: str, backend_url: str, supabase_auth: bool):
    """Start the AgentBeats frontend server"""
    
    # Validate backend_url requirement based on mode
    if frontend_mode in ["dev", "preview"] and not backend_url:
        print(f"Error: --backend_url is required for {frontend_mode} mode")
        sys.exit(1)
    # Find the frontend directory
    current_dir = pathlib.Path(__file__).parent.parent.parent  # Go up to project root
    frontend_dir = current_dir / "frontend" / webapp_version
    
    if not frontend_dir.exists():
        print(f"Error: Frontend directory not found at {frontend_dir}")
        print("Make sure you're running this from the AgentBeats project root.")
        print(f"Available frontend directories: {list((current_dir / 'frontend').glob('*'))}")
        sys.exit(1)

    # Check if frontend installed
    if not (frontend_dir / "node_modules").exists():
        print(f"Error: Frontend dependencies not installed for {webapp_version}. Run `agentbeats install_frontend --webapp_version {webapp_version}` to install them.")
        sys.exit(1)
    
    print(f"Starting AgentBeats Frontend ({webapp_version}) in {frontend_mode} mode...")
    print(f"Frontend directory: {frontend_dir}")
    if backend_url:
        print(f"Backend URL: {backend_url}")
    
    # Set environment variables
    env = os.environ.copy()
    if backend_url:  # Only set if backend_url is provided
        env["BACKEND_URL"] = backend_url
    if not supabase_auth:
        env["VITE_DEV_LOGIN"] = "true"
        print("🚀 Development mode enabled - dev login button will be shown")
    
    try:
        if frontend_mode == "dev":
            print(f"Development server will be available at http://{host}:{port}")
            print("Press Ctrl+C to stop the server")
            # Run development server
            subprocess.run(
                f"npm run dev -- --host {host} --port {str(port)}", 
                cwd=frontend_dir, check=True, shell=True, env=env
            )
            
        elif frontend_mode == "build":
            print(f"Building frontend ({webapp_version}) for production...")
            # Build for production
            subprocess.run("npm run build", cwd=frontend_dir, check=True, shell=True, env=env)
            print("Build completed successfully!")
            print(f"Built files are in {frontend_dir / 'build'}")
            
        elif frontend_mode == "preview":
            print(f"Building and previewing production build for {webapp_version}...")
            # First build
            subprocess.run("npm run build", cwd=frontend_dir, check=True, shell=True, env=env)
            # Then preview
            print(f"Preview server will be available at http://{host}:{port}")
            print("Press Ctrl+C to stop the server")
            subprocess.run(
                f"npm run preview -- --host {host} --port {str(port)}", 
                cwd=frontend_dir, check=True, shell=True, env=env
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

def _install_frontend(webapp_version: str):
    current_dir = pathlib.Path(__file__).parent.parent.parent  # Go up to project root
    frontend_dir = current_dir / "frontend" / webapp_version
    print(f"Installing frontend dependencies for {webapp_version}...")
    try:
        subprocess.run("npm install", cwd=frontend_dir, check=True, shell=True)
        print(f"Frontend dependencies installed successfully for {webapp_version}!")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Error installing frontend dependencies: {e}")
        sys.exit(1)


def _run_backend(host: str, backend_port: int, mcp_port: int, reload: bool, supabase_auth: bool, public_url: str):
    """Start the AgentBeats backend server and MCP server in the same terminal"""
    
    current_dir = pathlib.Path(__file__).parent.parent.parent  # Go up to project root
    mcp_server_path = current_dir / "src" / "backend" / "mcp" / "mcp_server.py"
    
    if not mcp_server_path.exists():
        print(f"Error: MCP server not found at {mcp_server_path}")
        sys.exit(1)
    
    # Global variables to track processes
    backend_process = None
    mcp_process = None
    
    def cleanup_mcp_process():
        """Clean up MCP process"""
        if mcp_process and mcp_process.poll() is None:  # Process is still running
            print("Cleaning up MCP process...")
            mcp_process.terminate()
            try:
                mcp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Force killing MCP process...")
                mcp_process.kill()
                mcp_process.wait()
    
    def start_backend():
        """Start the backend server"""
        nonlocal backend_process
        try:
            # Set environment variable for dev login mode
            if not supabase_auth:
                os.environ["DEV_LOGIN"] = "true"
                print("🚀 Development mode enabled - authentication will be bypassed for all API calls")

            if public_url and public_url != "None":
                os.environ["PUBLIC_BACKEND_URL"] = public_url
            else:
                os.environ["PUBLIC_BACKEND_URL"] = f"http://{host}:{backend_port}"
    
            print(f"Backend public URL configured as: {os.getenv('PUBLIC_BACKEND_URL')}")
            
            print(f"Starting AgentBeats Backend on http://{host}:{backend_port}")
            uvicorn.run(
                "backend.app:app",
                host=host,
                port=backend_port,
                reload=reload
            )
        except Exception as e:
            print(f"Error starting backend: {e}")
            print("Make sure all backend dependencies are installed.")
            # Ensure MCP process is cleaned up when backend fails
            cleanup_mcp_process()
            sys.exit(1)
    
    def start_mcp():
        """Start the MCP server"""
        nonlocal mcp_process
        try:
            print(f"Starting MCP server on port {mcp_port}")
            mcp_process = subprocess.Popen(
                [sys.executable, str(mcp_server_path),
                 "--host", str(host),
                 "--mcp_port", str(mcp_port),
                 "--backend_url", f"http://{host}:{backend_port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Print MCP server output
            try:
                for line in mcp_process.stdout:
                    if line:
                        print(f"[MCP] {line.rstrip()}")
                    # Check if process has terminated
                    if mcp_process.poll() is not None:
                        break
            except Exception as output_error:
                print(f"Error reading MCP output: {output_error}")
                
            # If we reach here and process has terminated, check return code
            if mcp_process.poll() is not None and mcp_process.returncode != 0:
                print(f"MCP server exited with code {mcp_process.returncode}")
                
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            print("Make sure the MCP server script is available and dependencies are installed.")
            # Set mcp_process to None to indicate failure
            mcp_process = None
    
    def signal_handler(signum, frame):
        """Handle Ctrl+C to gracefully shutdown both servers"""
        print("\nShutting down servers...")
        cleanup_mcp_process()
        sys.exit(0)
    
    # Register cleanup function to run on program exit
    atexit.register(cleanup_mcp_process)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting AgentBeats Backend and MCP Server...")
    print(f"Backend: http://{host}:{backend_port}")
    print(f"MCP Port: http://{host}:{mcp_port}")
    print("Press Ctrl+C to stop both servers")
    print("=" * 50)
    
    try:
        # Start MCP server in a separate thread
        mcp_thread = threading.Thread(target=start_mcp, daemon=True)
        mcp_thread.start()
        
        # Give MCP server a moment to start
        time.sleep(2)
        
        # Start backend server (blocking)
        start_backend()
    except Exception as e:
        print(f"Unexpected error: {e}")
        cleanup_mcp_process()
        sys.exit(1)
    finally:
        # Ensure cleanup even in unexpected termination
        cleanup_mcp_process()


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
    agent = BeatsAgent(name=__name__, 
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
    load_scenario_parser = sub_parser.add_parser("load_scenario", help="Launch a complete scenario from scenario.toml (agents, environment, etc.)")
    load_scenario_parser.add_argument("scenario_root", help="Path to scenario directory")
    load_scenario_parser.add_argument("--launch-mode", choices=["tmux", "separate", "current"], 
                                default="", help="Launching terminal; Will override scenario.toml's settings!")

    # run_scenario command
    run_scenario_parser = sub_parser.add_parser("run_scenario", help="Run a scenario from scenario.toml (requires frontend and backend to be running; eqivalant to `ab load_scenario` + register agent + start battle)")
    run_scenario_parser.add_argument("scenario_root", help="Path to scenario directory")
    run_scenario_parser.add_argument("--launch_mode", choices=["tmux", "separate", "current"],
                                default="", help="Launching terminal; Will override scenario.toml's settings!")
    run_scenario_parser.add_argument("--backend", help="Backend URL", default="http://localhost:9000")
    run_scenario_parser.add_argument("--frontend", help="Frontend URL", default="http://localhost:5173")

    # run_backend command
    backend_parser = sub_parser.add_parser("run_backend", help="Start the AgentBeats backend server")
    backend_parser.add_argument("--host", default="localhost", help="Backend host")
    backend_parser.add_argument("--backend_port", type=int, default=9000, help="Backend port (default: 9000)")
    backend_parser.add_argument("--mcp_port", type=int, default=9001, help=f"MCP port (default: 9001)")
    backend_parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    backend_parser.add_argument("--supabase_auth", action="store_true", help="Enable Supabase authentication (default: use dev login mode)")
    backend_parser.add_argument("--public_url", help="Public URL for backend (e.g., http://yourdomain.com:9000).")

    # run_frontend command
    frontend_parser = sub_parser.add_parser("run_frontend", help="Start the AgentBeats frontend server")
    frontend_parser.add_argument("--frontend_mode", choices=["dev", "build", "preview"], default="dev", 
                                help="Frontend mode: dev (development), build (production build), preview (build + preview), install (install dependencies)")
    frontend_parser.add_argument("--host", default="localhost", help="Frontend host (default: localhost)")
    frontend_parser.add_argument("--frontend_port", type=int, default=5173, help="Frontend port (default: 5173)")
    frontend_parser.add_argument("--webapp_version", default="webapp-v2", help="Frontend webapp version to run (default: webapp)")
    frontend_parser.add_argument("--backend_url", help="Backend URL for API proxy (required for dev and preview modes)")
    frontend_parser.add_argument("--supabase_auth", action="store_true", help="Enable Supabase authentication (default: use dev login mode)")

    frontend_install_parser = sub_parser.add_parser("install_frontend", help="Install frontend dependencies")
    frontend_install_parser.add_argument("--webapp_version", default="webapp-v2", help="Frontend webapp version to install (default: webapp-v2)")

    # deploy command
    deploy_parser = sub_parser.add_parser("deploy", help="Deploy complete AgentBeats stack (backend + frontend + MCP)")
    deploy_parser.add_argument("--deploy_mode", choices=["dev", "build"], default="dev",
                              help="Deployment mode: dev (development) or build (production)")
    deploy_parser.add_argument("--launch_mode", choices=["current", "separate", "tmux"], default="current",
                              help="Launch mode: current (same terminal), separate (separate terminals), tmux (tmux session)")
    deploy_parser.add_argument("--backend_port", type=int, default=9000, help="Backend port (default: 9000)")
    deploy_parser.add_argument("--frontend_port", type=int, default=5173, help="Frontend port (default: 5173)")
    deploy_parser.add_argument("--mcp_port", type=int, default=9001, help="MCP server port (default: 9001)")
    deploy_parser.add_argument("--supabase_auth", action="store_true", help="Enable Supabase authentication (default: use dev login mode)")
    deploy_parser.add_argument("--public_url", help="Public URL for backend (e.g., http://yourdomain.com:9000).", default=None)

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
        launcher = BeatsAgentLauncher(agent_card=args.card,
                                      launcher_host=args.launcher_host,
                                      launcher_port=args.launcher_port,
                                      agent_host=args.agent_host,
                                      agent_port=args.agent_port,
                                      model_type=args.model_type,
                                      model_name=args.model_name,
                                      mcp_list=args.mcp,
                                      tool_list=args.tool)
        launcher.run(reload=args.reload)
    
    elif args.cmd == "load_scenario":
        manager = ScenarioManager(scenario_root=pathlib.Path(args.scenario_root))
        manager.load_scenario(mode=args.launch_mode)
    
    elif args.cmd == "run_scenario":
        manager = ScenarioManager(scenario_root=pathlib.Path(args.scenario_root))
        manager.load_scenario(mode=args.launch_mode)
        time.sleep(10) # TODO: should check aliveness here; can implement later
        manager.start_battle(backend_url=args.backend, 
                             frontend_url=args.frontend)

    elif args.cmd == "run_backend":
        _run_backend(host=args.host, backend_port=args.backend_port, mcp_port=args.mcp_port, reload=args.reload, supabase_auth=args.supabase_auth, public_url=args.public_url)
    elif args.cmd == "run_frontend":
        _run_frontend(frontend_mode=args.frontend_mode, host=args.host, port=args.frontend_port, webapp_version=args.webapp_version, backend_url=args.backend_url, supabase_auth=args.supabase_auth)
    elif args.cmd == "install_frontend":
        _install_frontend(webapp_version=args.webapp_version)
    elif args.cmd == "deploy":
        _run_deploy(deploy_mode=args.deploy_mode, backend_port=args.backend_port, 
                   frontend_port=args.frontend_port, mcp_port=args.mcp_port, 
                   launch_mode=args.launch_mode, supabase_auth=args.supabase_auth, public_url=args.public_url)
    
    elif args.cmd == "check":
        _check_environment()
