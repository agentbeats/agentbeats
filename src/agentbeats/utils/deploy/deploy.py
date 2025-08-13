
import sys
import pathlib
import subprocess
import time
import signal
import atexit
import platform
import os

def _deploy_current_terminal(deploy_mode: str, backend_port: int, frontend_port: int, mcp_port: int, current_dir: pathlib.Path, mcp_server_path: pathlib.Path, supabase_auth: bool, public_url: str = None):
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
        if deploy_mode == "build":
            try:
                subprocess.run("pm2 delete agentbeats-ssr", shell=True, capture_output=True)
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
        if deploy_mode == "build":
            backend_cmd = [
                sys.executable, "-m", "agentbeats", "run_backend",
                "--host", "127.0.0.1",
                "--backend_port", str(backend_port),
                "--mcp_port", str(mcp_port)
            ]
        elif deploy_mode == "dev":
            backend_cmd = [
                sys.executable, "-m", "agentbeats", "run_backend",
                "--host", "localhost",
                "--backend_port", str(backend_port),
                "--mcp_port", str(mcp_port),
                # "--reload"
            ]

        if supabase_auth:
            backend_cmd.append("--supabase_auth")

        if public_url:
            backend_cmd.append("--public_url")
            backend_cmd.append(public_url)
            
        backend_proc = subprocess.Popen(backend_cmd)
        processes.append(backend_proc)
        time.sleep(3)  # Give backend time to start
        
        
        # 2. Start Frontend using CLI command
        print(f"Starting Frontend in {deploy_mode} mode on port {frontend_port}...")
        if deploy_mode == "dev":
            frontend_cmd = [
                sys.executable, "-m", "agentbeats", "run_frontend",
                "--frontend_mode", "dev",
                "--host", "localhost", 
                "--frontend_port", str(frontend_port),
                "--backend_url", f"http://localhost:{backend_port}"
            ]
            if supabase_auth:
                frontend_cmd.append("--supabase_auth")
            frontend_proc = subprocess.Popen(frontend_cmd)
            processes.append(frontend_proc)
        elif deploy_mode == "build":
            # Build first, then start with PM2 or preview
            build_cmd = [
                sys.executable, "-m", "agentbeats", "run_frontend",
                "--frontend_mode", "build",
            ]
            if supabase_auth:
                build_cmd.append("--supabase_auth")
            build_proc = subprocess.Popen(build_cmd)
            build_proc.wait()  # Wait for build to complete
            
            # Check if PM2 is available for production mode
            try:
                subprocess.run("pm2 --version", check=True, capture_output=True, shell=True)
                print(f"[Production] Starting frontend with PM2...")
                
                # Use existing production server setup logic
                frontend_dir = current_dir / "frontend" / "webapp-v2"
                subprocess.run("pm2 delete agentbeats-ssr", shell=True, capture_output=True)
                subprocess.run(
                    f"pm2 start {frontend_dir / 'build' / 'index.js'} --name agentbeats-ssr --no-daemon",  
                    cwd=frontend_dir, check=True, shell=True
                )
                print("[Success] Frontend started with PM2")
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("[Warning] PM2 not found, starting with preview mode...")
                preview_cmd = [
                    "agentbeats", "run_frontend",
                    "--frontend_mode", "preview",
                    "--host", "localhost",
                    "--frontend_port", str(frontend_port),
                    "--backend_url", f"http://localhost:{backend_port}"
                ]
                frontend_proc = subprocess.Popen(preview_cmd)
                processes.append(frontend_proc)
        
        # 4. Display status
        time.sleep(2)
        print("\n" + "=" * 50)
        print("[Status] AgentBeats Deployment Status:")
        print("=" * 50)
        if deploy_mode == "build":
            print(f"[Frontend] http://localhost:3000")
        else:
            print(f"[Frontend] http://localhost:{frontend_port}")
            
        print(f"[Backend]  http://localhost:{backend_port}")
        print(f"[MCP]      http://localhost:{mcp_port}")
        print("=" * 50)
        print("Press Ctrl+C to stop all services")
        
        # 5. Monitor processes (only for dev mode, build mode uses PM2)
        if deploy_mode == "dev":
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


def _deploy_separate_terminals(deploy_mode: str, backend_port: int, frontend_port: int, mcp_port: int, current_dir: pathlib.Path, mcp_server_path: pathlib.Path, supabase_auth: bool, public_url: str = None):
    """Deploy each service in a separate terminal window"""
   
    print("Starting services in separate terminals...")
    
    system = platform.system()
    
    # Commands for each service
    backend_cmd = f"{sys.executable} -m agentbeats run_backend --host {'127.0.0.1' if deploy_mode == 'build' else 'localhost'} --backend_port {backend_port} --mcp_port {mcp_port}"
    if deploy_mode == "dev":
        backend_cmd += " --reload"
    if supabase_auth:
        backend_cmd += " --supabase_auth"
    if public_url:
        backend_cmd += f" --public_url {public_url}"


    # Frontend command depends on mode
    if deploy_mode == "dev":
        frontend_cmd = f"{sys.executable} -m agentbeats run_frontend --frontend_mode dev --host localhost --frontend_port {frontend_port} --backend_url http://localhost:{backend_port}"
        if supabase_auth:
            frontend_cmd += " --supabase_auth"
    else:  # build mode
        # Check if PM2 is available for production mode
        try:
            subprocess.run("pm2 --version", check=True, capture_output=True, shell=True)
            print(f"[Production] PM2 detected, will use PM2 for frontend...")
            
            # Build first, then start with PM2
            build_cmd = f"{sys.executable} -m agentbeats run_frontend --frontend_mode build"
            if supabase_auth:
                build_cmd += " --supabase_auth"
            frontend_dir = current_dir / "frontend" / "webapp-v2"
            if system == "Windows":
                pm2_cmd = f"pm2 delete agentbeats-ssr 2>nul || echo Cleaned && pm2 start {frontend_dir / 'build' / 'index.js'} --name agentbeats-ssr --no-daemon"
            else:
                pm2_cmd = f"pm2 delete agentbeats-ssr 2>/dev/null || true && pm2 start {frontend_dir / 'build' / 'index.js'} --name agentbeats-ssr --no-daemon"
            frontend_cmd = f"{build_cmd} && {pm2_cmd}"
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[Warning] PM2 not found, using preview mode...")
            frontend_cmd = f"{sys.executable} -m agentbeats run_frontend --frontend_mode preview --host localhost --frontend_port {frontend_port} --backend_url http://localhost:{backend_port}"
    
    services = [
        ("Backend", backend_cmd),
        ("Frontend", frontend_cmd)
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
    if deploy_mode == "build":
        print(f"[Frontend] http://localhost:3000")
        print(f"[Frontend] Running with PM2 (use 'pm2 logs agentbeats-ssr' for logs)")
    else:
        print(f"[Frontend] http://localhost:{frontend_port}")
    print(f"[MCP]      http://localhost:{mcp_port}")
    print("=" * 50)
    print("Each service is running in its own terminal window.")
    if deploy_mode == "build":
        print("Frontend is managed by PM2. Use 'pm2 list' to check status.")
        print("Use 'pm2 stop agentbeats-ssr' to stop frontend.")


def _deploy_tmux(deploy_mode: str, backend_port: int, frontend_port: int, mcp_port: int, current_dir: pathlib.Path, mcp_server_path: pathlib.Path, supabase_auth: bool, public_url: str = None):
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
        backend_cmd = f"{sys.executable} -m agentbeats run_backend --host {'127.0.0.1' if deploy_mode == 'build' else 'localhost'} --backend_port {backend_port} --mcp_port {mcp_port}"
        if deploy_mode == "dev":
            backend_cmd += " --reload"
        if supabase_auth:
            backend_cmd += " --supabase_auth"
        if public_url:
            backend_cmd += f" --public_url {public_url}"
            
        # Frontend command depends on mode
        if deploy_mode == "dev":
            frontend_cmd = f"{sys.executable} -m agentbeats run_frontend --frontend_mode dev --host localhost --frontend_port {frontend_port} --backend_url http://localhost:{backend_port}"
        else:  # build mode
            # Check if PM2 is available for production mode
            try:
                subprocess.run("npx pm2 --version", check=True, capture_output=True, shell=True)
                print(f"[Production] npx pm2 detected, will use PM2 for frontend in tmux...")
                
                # Build first, then start with PM2
                build_cmd = f"{sys.executable} -m agentbeats run_frontend --frontend_mode build"
                if supabase_auth:
                    build_cmd += " --supabase_auth"
                frontend_dir = current_dir / "frontend" / "webapp-v2"
                pm2_cmd = f"npx pm2 delete agentbeats-ssr 2>/dev/null || true && npx pm2 start {frontend_dir / 'build' / 'index.js'} --name agentbeats-ssr --no-daemon"
                frontend_cmd = f"echo 'Building frontend...' && {build_cmd} && echo 'Starting with PM2...' && {pm2_cmd} && echo 'Frontend started with PM2. Use pm2 logs agentbeats-ssr to see logs.'"
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("[Warning] PM2 not found in tmux mode, using preview mode...")
                frontend_cmd = f"{sys.executable} -m agentbeats run_frontend --frontend_mode preview --host localhost --frontend_port {frontend_port} --backend_url http://localhost:{backend_port}"

                if supabase_auth:
                    frontend_cmd += " --supabase_auth"
    
        # Start services in each pane
        subprocess.run([
            "tmux", "send-keys", "-t", f"{session_name}:0.0",
            f"echo 'Starting Backend...' && {backend_cmd}", "Enter"
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
        if deploy_mode == "build":
            print(f"[Frontend] http://localhost:3000 (Bottom right pane)")
            print(f"[Frontend] Running with PM2 (use 'npx pm2 logs agentbeats-ssr' for logs)")
        else:
            print(f"[Frontend] http://localhost:{frontend_port} (Bottom right pane)")
        print("=" * 50)
        print(f"To attach to tmux session: tmux attach-session -t {session_name}")
        print(f"To kill tmux session: tmux kill-session -t {session_name}")
        if deploy_mode == "build":
            print("Frontend is managed by PM2. Use 'npx pm2 list' to check status.")
            print("Use 'npx pm2 stop agentbeats-ssr' to stop frontend.")
        print("In tmux: Ctrl+B then D to detach, Ctrl+B then X to close pane")
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting up tmux session: {e}")
        print("Falling back to current terminal mode...")
        _deploy_current_terminal(deploy_mode, backend_port, frontend_port, mcp_port, current_dir, mcp_server_path)