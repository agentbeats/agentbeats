
import sys
import pathlib
import subprocess
import time
import signal
import atexit
import platform
import os

def _deploy_current_terminal(mode: str, backend_port: int, frontend_port: int, mcp_port: int, current_dir: pathlib.Path, mcp_server_path: pathlib.Path):
    """Deploy all services in the current terminal (original behavior)"""
    
    # Store process references for cleanup
    processes = []
    
    def cleanup_processes():
        """Clean up all spawned processes"""
        print("\nCleaning up processes...")
        for proc in processes:
            if proc.poll() is None:  # Process is still running
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        
        # Also cleanup PM2 processes if in build mode
        if mode == "build":
            try:
                subprocess.run(["pm2", "delete", "agentbeats-ssr"], shell=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
    
    # Register cleanup function
    atexit.register(cleanup_processes)
    
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        cleanup_processes()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. Start Backend using CLI command
        print(f"Starting Backend on port {backend_port}...")
        if mode == "build":
            backend_cmd = [
                "agentbeats", "run_backend",
                "--host", "127.0.0.1",
                "--port", str(backend_port)
            ]
        elif mode == "dev":
            backend_cmd = [
                "agentbeats", "run_backend",
                "--host", "0.0.0.0",
                "--port", str(backend_port),
                "--reload"
            ]
            
        backend_proc = subprocess.Popen(backend_cmd)
        processes.append(backend_proc)
        time.sleep(3)  # Give backend time to start
        
        # 2. Start MCP Server
        print(f"Starting MCP Server on port {mcp_port}...")
        mcp_env = os.environ.copy()
        mcp_env["MCP_PORT"] = str(mcp_port)
        mcp_proc = subprocess.Popen([
            sys.executable, str(mcp_server_path)
        ], env=mcp_env, cwd=current_dir)
        processes.append(mcp_proc)
        time.sleep(1)  # Give MCP server time to start
        
        # 3. Start Frontend using CLI command
        print(f"Starting Frontend in {mode} mode on port {frontend_port}...")
        if mode == "dev":
            frontend_cmd = [
                "agentbeats", "run_frontend",
                "--mode", "dev",
                "--host", "0.0.0.0", 
                "--port", str(frontend_port)
            ]
            frontend_proc = subprocess.Popen(frontend_cmd)
            processes.append(frontend_proc)
        elif mode == "build":
            # Build first, then start with PM2 or preview
            build_cmd = [
                "agentbeats", "run_frontend",
                "--mode", "build",
                "--host", "127.0.0.1",
                "--port", str(frontend_port)
            ]
            build_proc = subprocess.Popen(build_cmd)
            build_proc.wait()  # Wait for build to complete
            
            # Check if PM2 is available for production mode
            try:
                subprocess.run(["pm2", "--version"], check=True, capture_output=True, shell=True)
                print(f"[Production] Starting frontend with PM2...")
                
                # Use existing production server setup logic
                frontend_dir = current_dir / "frontend" / "webapp"
                subprocess.run(["pm2", "delete", "agentbeats-ssr"], shell=True, capture_output=True)
                subprocess.run([
                    "pm2", "start", str(frontend_dir / "build" / "index.js"),
                    "--name", "agentbeats-ssr",
                    "--", "--port", str(frontend_port)
                ], cwd=frontend_dir, check=True, shell=True)
                print("[Success] Frontend started with PM2")
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("[Warning] PM2 not found, starting with preview mode...")
                preview_cmd = [
                    sys.executable, "-m", "agentbeats", "run_frontend",
                    "--mode", "preview",
                    "--host", "0.0.0.0",
                    "--port", str(frontend_port)
                ]
                frontend_proc = subprocess.Popen(preview_cmd)
                processes.append(frontend_proc)
        
        # 4. Display status
        time.sleep(2)
        print("\n" + "=" * 50)
        print("[Status] AgentBeats Deployment Status:")
        print("=" * 50)
        print(f"[Backend]  http://localhost:{backend_port}")
        print(f"[Frontend] http://localhost:{frontend_port}")
        print(f"[MCP]      http://localhost:{mcp_port}")
        print("=" * 50)
        print("Press Ctrl+C to stop all services")
        
        # 5. Monitor processes (only for dev mode, build mode uses PM2)
        if mode == "dev":
            while True:
                time.sleep(1)
                # Check if any critical process died
                for i, proc in enumerate(processes):
                    if proc.poll() is not None:
                        service_names = ["Backend", "MCP", "Frontend"]
                        if i < len(service_names):
                            print(f"[Error] {service_names[i]} process died!")
                        break
                else:
                    continue
                break
        else:
            print("[Info] Services started. Use 'pm2 list' to check frontend status.")
            print("[Info] Use 'pm2 logs agentbeats-ssr' to check frontend logs.")
            # For build mode, just keep backend and MCP running
            while True:
                time.sleep(1)
                if backend_proc.poll() is not None:
                    print("[Error] Backend process died!")
                    break
                if mcp_proc.poll() is not None:
                    print("[Error] MCP process died!")
                    break
                
    except subprocess.CalledProcessError as e:
        print(f"[Error] Error during deployment: {e}")
        cleanup_processes()
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"[Error] Command not found: {e}")
        print("Make sure Node.js, npm, and Python are installed.")
        cleanup_processes()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStop: Deployment interrupted by user")
        cleanup_processes()
        sys.exit(0)


def _deploy_separate_terminals(mode: str, backend_port: int, frontend_port: int, mcp_port: int, current_dir: pathlib.Path, mcp_server_path: pathlib.Path):
    """Deploy each service in a separate terminal window"""

    
    print("Starting services in separate terminals...")
    
    system = platform.system()
    
    # Commands for each service
    services = [
        ("Backend", f"agentbeats run_backend --host {'127.0.0.1' if mode == 'build' else '0.0.0.0'} --port {backend_port}" + (" --reload" if mode == "dev" else "")),
        ("MCP Server", f"set MCP_PORT={mcp_port} && {sys.executable} \"{mcp_server_path}\"" if system == "Windows" else f"MCP_PORT={mcp_port} {sys.executable} \"{mcp_server_path}\""),
        ("Frontend", f"agentbeats run_frontend --mode {mode} --host {'127.0.0.1' if mode == 'build' else '0.0.0.0'} --port {frontend_port}")
    ]
    
    for name, cmd in services:
        print(f"Starting {name} in new terminal...")
        
        if system == "Windows":
            # Windows command
            full_cmd = f'start cmd /k "title AgentBeats-{name} && {cmd}"'
            subprocess.Popen(full_cmd, shell=True, cwd=current_dir)
            
        elif system == "Darwin":  # macOS
            apple_script = f'''
            tell application "Terminal"
                do script "cd '{current_dir}' && {cmd}"
            end tell
            '''
            subprocess.Popen(['osascript', '-e', apple_script])
            
        else:  # Linux
            # Try different terminal emulators
            terminal_cmds = [
                ['gnome-terminal', '--', 'bash', '-c'],
                ['xterm', '-e', 'bash', '-c'],
                ['konsole', '-e', 'bash', '-c'],
                ['xfce4-terminal', '-e', 'bash', '-c']
            ]
            
            full_cmd = f'cd "{current_dir}" && {cmd}; exec bash'
            
            terminal_opened = False
            for term_cmd in terminal_cmds:
                try:
                    subprocess.Popen(term_cmd + [full_cmd])
                    terminal_opened = True
                    break
                except FileNotFoundError:
                    continue
            
            if not terminal_opened:
                print(f"Warning: Could not open terminal for {name}. Please run manually: {cmd}")
        
        time.sleep(1)  # Small delay between opening terminals
    
    print("\n" + "=" * 50)
    print("[Status] AgentBeats Services Started in Separate Terminals:")
    print("=" * 50)
    print(f"[Backend]  http://localhost:{backend_port}")
    print(f"[Frontend] http://localhost:{frontend_port}")
    print(f"[MCP]      http://localhost:{mcp_port}")
    print("=" * 50)
    print("Each service is running in its own terminal window.")
    print("Close terminal windows individually to stop services.")


def _deploy_tmux(mode: str, backend_port: int, frontend_port: int, mcp_port: int, current_dir: pathlib.Path, mcp_server_path: pathlib.Path):
    """Deploy services in tmux session with split panes"""
    
    # Check if tmux is available
    try:
        subprocess.run(["tmux", "-V"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: tmux is not installed or not available.")
        print("Please install tmux or use a different launch mode.")
        sys.exit(1)
    
    print("Starting services in tmux session...")
    
    session_name = "agentbeats"
    
    # Kill existing session if it exists
    try:
        subprocess.run(["tmux", "kill-session", "-t", session_name], 
                      capture_output=True, check=False)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    try:
        # Create new tmux session
        subprocess.run([
            "tmux", "new-session", "-d", "-s", session_name,
            "-c", str(current_dir)
        ], check=True)
        
        # Split into 3 panes
        # Split horizontally (top and bottom)
        subprocess.run([
            "tmux", "split-window", "-h", "-t", f"{session_name}:0"
        ], check=True)
        
        # Split the right pane vertically
        subprocess.run([
            "tmux", "split-window", "-v", "-t", f"{session_name}:0.1"
        ], check=True)
        
        # Commands for each pane
        backend_cmd = f"agentbeats run_backend --host {'127.0.0.1' if mode == 'build' else '0.0.0.0'} --port {backend_port}" + (" --reload" if mode == "dev" else "")
        mcp_cmd = f"MCP_PORT={mcp_port} {sys.executable} \"{mcp_server_path}\""
        frontend_cmd = f"agentbeats run_frontend --mode {mode} --host {'127.0.0.1' if mode == 'build' else '0.0.0.0'} --port {frontend_port}"
        
        # Start services in each pane
        subprocess.run([
            "tmux", "send-keys", "-t", f"{session_name}:0.0",
            f"echo 'Starting Backend...' && {backend_cmd}", "Enter"
        ], check=True)
        
        subprocess.run([
            "tmux", "send-keys", "-t", f"{session_name}:0.1", 
            f"echo 'Starting MCP Server...' && {mcp_cmd}", "Enter"
        ], check=True)
        
        subprocess.run([
            "tmux", "send-keys", "-t", f"{session_name}:0.2",
            f"echo 'Starting Frontend...' && {frontend_cmd}", "Enter"
        ], check=True)
        
        # Set pane titles
        subprocess.run([
            "tmux", "select-pane", "-t", f"{session_name}:0.0", "-T", "Backend"
        ], check=True)
        subprocess.run([
            "tmux", "select-pane", "-t", f"{session_name}:0.1", "-T", "MCP"
        ], check=True)
        subprocess.run([
            "tmux", "select-pane", "-t", f"{session_name}:0.2", "-T", "Frontend"
        ], check=True)
        
        time.sleep(2)
        
        print("\n" + "=" * 50)
        print("[Status] AgentBeats Services Started in tmux:")
        print("=" * 50)
        print(f"[Backend]  http://localhost:{backend_port} (Left pane)")
        print(f"[MCP]      http://localhost:{mcp_port} (Top right pane)")
        print(f"[Frontend] http://localhost:{frontend_port} (Bottom right pane)")
        print("=" * 50)
        print(f"To attach to tmux session: tmux attach-session -t {session_name}")
        print(f"To kill tmux session: tmux kill-session -t {session_name}")
        print("In tmux: Ctrl+B then D to detach, Ctrl+B then X to close pane")
        
        # Attach to the session
        print(f"\nAttaching to tmux session '{session_name}'...")
        print("Press Ctrl+B then D to detach from tmux session")
        subprocess.run(["tmux", "attach-session", "-t", session_name])
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting up tmux session: {e}")
        print("Falling back to current terminal mode...")
        _deploy_current_terminal(mode, backend_port, frontend_port, mcp_port, current_dir, mcp_server_path)