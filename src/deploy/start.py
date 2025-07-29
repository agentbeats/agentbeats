#!/usr/bin/env python3
"""
AgentBeats Development Server Startup Script
Supports Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import threading
import time
import argparse
import shutil
from pathlib import Path


def check_environment():
    """Check if the environment is properly set up"""
    print("Checking environment...")
    
    issues = []
    
    # Check if in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        issues.append("❌ Virtual environment not activated. Please activate with 'source venv/bin/activate' or 'venv\\Scripts\\activate'")
    else:
        print("✅ Virtual environment is active")
    
    # Check Python version
    if sys.version_info < (3, 11):
        issues.append("❌ Python 3.11+ required")
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is supported")
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ Node.js is installed: {result.stdout.strip()}")
        else:
            issues.append("❌ Node.js not found")
    except FileNotFoundError:
        issues.append("❌ Node.js not found. Please install Node.js")
    
    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ npm is installed: {result.stdout.strip()}")
        else:
            issues.append("❌ npm not found")
    except FileNotFoundError:
        issues.append("❌ npm not found. Please install npm")
    
    # Check OpenAI API key
    key_set = 0
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("⚠️ OPENAI_API_KEY environment variable not set")
    elif not openai_key.startswith('sk-'):
        print("⚠️ OPENAI_API_KEY should start with 'sk-'")
    else:
        print("✅ OPENAI_API_KEY is set")
        key_set += 1

    # Check OpenRouter API key
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_key:
        print("⚠️ OPENROUTER_API_KEY environment variable not set")
        
    elif not openrouter_key.startswith('sk-'):
        print("⚠️ OPENROUTER_API_KEY should start with 'sk-'")
    else:
        print("✅ OPENROUTER_API_KEY is set")
        key_set += 1

    if key_set == 0:
        issues.append("❌ At least one API key (OPENAI_API_KEY or OPENROUTER_API_KEY) must be set")
    
    # Check required directories
    required_dirs = ['src/agentbeats_backend', 'src/agentbeats_backend/mcp', 'frontend/webapp-v2']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            issues.append(f"❌ Required directory not found: {dir_path}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    # Check required files
    required_files = ['src/agentbeats_backend/run.py', 'src/agentbeats_backend/mcp/mcp_server.py', 'frontend/webapp-v2/package.json']
    for file_path in required_files:
        if not os.path.exists(file_path):
            issues.append(f"❌ Required file not found: {file_path}")
        else:
            print(f"✅ File exists: {file_path}")
    
    # Check if webapp-v2 dependencies are installed
    if os.path.exists('frontend/webapp-v2/node_modules'):
        print("✅ Frontend dependencies are installed")
    else:
        issues.append("❌ Frontend dependencies not installed. Run 'cd webapp-v2 && npm install'")
    
    return issues


def start_in_current_terminal():
    """Start all services in the current terminal"""
    print("Starting services in current terminal...")
    
    # Create a list to store processes
    processes = []
    
    try:
        # Start backend
        print("Starting backend server...")
        backend_process = subprocess.Popen(
            [sys.executable, '-m', 'src.agentbeats_backend.run'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(('Backend', backend_process))
        
        # Start MCP server
        print("Starting MCP server...")
        mcp_process = subprocess.Popen(
            [sys.executable, 'src/agentbeats_backend/mcp/mcp_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(('MCP', mcp_process))
        
        # Start frontend
        print("Starting frontend server...")
        frontend_process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd='frontend/webapp-v2',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=True
        )
        processes.append(('Frontend', frontend_process))
        
        # Create threads to handle output from each process
        def handle_output(name, process):
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"[{name}] {output.strip()}")
        
        threads = []
        for name, process in processes:
            thread = threading.Thread(target=handle_output, args=(name, process))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        print("\nAll services started! Press Ctrl+C to stop all services.")
        print("Services running on:")
        print("- Backend: http://localhost:9000")
        print("- MCP Server: http://localhost:9001")
        print("- Frontend: http://localhost:5173")
        
        # Wait for all processes
        for name, process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\nShutting down services...")
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            process.wait()
        print("All services stopped.")


def start_in_separate_terminals():
    """Start each service in a separate terminal window"""
    print("Starting services in separate terminals...")
    
    system = platform.system()
    
    # Commands for each service
    commands = [
        ("Backend", f"{sys.executable} -m src.agentbeats_backend.run"),
        ("MCP Server", f"{sys.executable} src/agentbeats_backend/mcp/mcp_server.py"),
        ("Frontend", "npm run dev")
    ]
    
    for name, cmd in commands:
        print(f"Starting {name} in new terminal...")
        
        if system == "Windows":
            # Windows command
            if name == "Frontend":
                # For frontend, we need to change to webapp-v2 directory first
                full_cmd = f'start cmd /k "title {name} && cd webapp-v2 && {cmd}"'
            else:
                full_cmd = f'start cmd /k "title {name} && {cmd}"'
            subprocess.Popen(full_cmd, shell=True)
            
        elif system == "Darwin":  # macOS TODO: not validated yet
            # macOS command
            if name == "Frontend":
                full_cmd = f'cd frontend/webapp-v2 && {cmd}'
            else:
                full_cmd = cmd
            
            apple_script = f'''
            tell application "Terminal"
                do script "cd '{os.getcwd()}' && {full_cmd}"
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
            
            if name == "Frontend":
                full_cmd = f'cd frontend/webapp-v2 && {cmd}; exec bash'
            else:
                full_cmd = f'{cmd}; exec bash'
            
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
    
    print("\nAll services started in separate terminals!")
    print("Services should be running on:")
    print("- Backend: http://localhost:9000")
    print("- MCP Server: http://localhost:9001")
    print("- Frontend: http://localhost:5173")


def main():
    parser = argparse.ArgumentParser(description='AgentBeats Development Server Startup Script')
    parser.add_argument('--separate', action='store_true', 
                       help='Start each service in a separate terminal window')
    parser.add_argument('--check', action='store_true',
                       help='Only check environment configuration')
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not os.path.exists('src') or not os.path.exists('frontend'):
        print("Error: Please run this script from the AgentBeats project root directory")
        sys.exit(1)
    
    # Always check environment first
    issues = check_environment()
    
    if issues:
        print("\n⚠️  Environment Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        
        if args.check:
            sys.exit(1)
        
        print("\nPlease fix the issues above before starting the services.")
        sys.exit(1)
    
    print("\n✅ Environment check passed!")
    
    # If only checking, exit here
    if args.check:
        print("Environment is properly configured.")
        return
    
    # Start services
    if args.separate:
        start_in_separate_terminals()
    else:
        start_in_current_terminal()


if __name__ == "__main__":
    main()
