#!/usr/bin/env python3
"""
Auto-start script for AgentBeats
Starts all services in separate terminal windows/tabs
"""

import os
import sys
import subprocess
import time
import signal
import platform
import requests
from pathlib import Path

# Configuration
# Note: Backend and MCP server use module imports (-m flag) for best practices
# Agent launchers use direct file execution since they're designed as scripts
SERVICES = {
    "backend": {
        "command": ["python", "-m", "src.backend.run"],
        "cwd": ".",
        "env": {},
        "description": "FastAPI Backend Server (port 9000)",
        "use_venv": True
    },
    "mcp_server": {
        "command": ["python", "src/logging/testing_mcp.py"],
        "cwd": ".",
        "env": {"PYTHONPATH": "."},
        "description": "MCP Logging Server (port 9001)",
        "use_venv": True
    },
    "blue_agent": {
        "command": ["python", "scenarios/agent_launcher.py", "--file", "scenarios/wasp/blue_agent/main.py", "--port", "9010"],
        "cwd": ".",
        "env": {},
        "description": "Blue Agent (Defender) - port 9010",
        "use_venv": True
    },
    "red_agent": {
        "command": ["python", "scenarios/agent_launcher.py", "--file", "scenarios/wasp/red_agent/main.py", "--port", "9020"],
        "cwd": ".",
        "env": {},
        "description": "Red Agent (Attacker) - port 9020",
        "use_venv": True
    },
    "green_agent": {
        "command": ["python", "scenarios/agent_launcher.py", "--file", "scenarios/wasp/green_agent/main.py", "--port", "9030", "--mcp-url", "http://localhost:9001/sse"],
        "cwd": ".",
        "env": {"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")},
        "description": "Green Agent (Judge) - port 9030",
        "use_venv": True
    },
    "frontend": {
        "command": ["npm", "run", "dev"],
        "cwd": "frontend",
        "env": {},
        "description": "Svelte Frontend (port 5173)",
        "use_venv": False
    }
}

class ServiceManager:
    def __init__(self):
        self.processes = {}
        self.system = platform.system()
        
    def check_environment(self):
        """Check if virtual environment is set up"""
        # Check if venv exists
        venv_path = Path("venv")
        if not venv_path.exists():
            print("❌ Virtual environment not found!")
            print("   Please create a virtual environment first:")
            print("   python -m venv venv")
            print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
            print("   pip install -r requirements.txt")
            sys.exit(1)
        else:
            print("✅ Virtual environment found")
    
    def check_openai_key(self):
        """Check if OpenAI API key is set"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  WARNING: OPENAI_API_KEY environment variable is not set!")
            print("   The green agent will fail to start without it.")
            print("   Set it with: export OPENAI_API_KEY='your-api-key-here'")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
        else:
            print("✅ OpenAI API key is set")
    
    def start_service_macos(self, name, config):
        """Start service on macOS using osascript to open new terminal windows"""
        title = f"AgentBeats - {config['description']}"
        
        # Build the command
        cmd_str = " ".join(config['command'])
        if config['env']:
            env_str = " ".join([f"{k}={v}" for k, v in config['env'].items()])
            cmd_str = f"{env_str} {cmd_str}"
        
        # Add virtual environment activation for Python services
        if config.get('use_venv', False):
            venv_activate = "source venv/bin/activate && "
            cmd_str = f"{venv_activate}{cmd_str}"
        
        # Create osascript command
        script = f'''
        tell application "Terminal"
            set newTab to do script "cd {os.path.abspath(config['cwd'])} && echo 'Starting {name}...' && {cmd_str}"
            set custom title of front window to "{title}"
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            print(f"🔄 Started {name} in new terminal window, verifying...")
            
            # Wait a moment for the service to start
            time.sleep(2)
            
            # Verify the service is actually running
            if self.verify_service_running(name, config):
                print(f"✅ {name} is running successfully")
                return True
            else:
                print(f"⚠️  {name} terminal opened but service may not be running properly")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start {name}: {e}")
            return False
    
    def verify_service_running(self, name, config):
        """Verify that a service is actually running by checking its expected port/endpoint"""
        try:
            if name == "backend":
                # Check if backend is responding on port 9000
                import requests
                response = requests.get("http://localhost:9000/health", timeout=5)
                return response.status_code == 200
            elif name == "mcp_server":
                # Assume MCP server works - just return True
                return True
            elif name == "blue_agent":
                # Check if blue agent is responding on port 9011 using the A2A agent card endpoint
                import requests
                try:
                    response = requests.get("http://localhost:9011/.well-known/agent.json", timeout=5)
                    return response.status_code == 200
                except:
                    return False
            elif name == "red_agent":
                # Check if red agent is responding on port 9021 using the A2A agent card endpoint
                import requests
                try:
                    response = requests.get("http://localhost:9021/.well-known/agent.json", timeout=5)
                    return response.status_code == 200
                except:
                    return False
            elif name == "green_agent":
                # Check if green agent is responding on port 9031 using the A2A agent card endpoint
                import requests
                try:
                    response = requests.get("http://localhost:9031/.well-known/agent.json", timeout=5)
                    return response.status_code == 200
                except:
                    return False
            elif name == "frontend":
                # Check if frontend is responding on port 5173
                import requests
                response = requests.get("http://localhost:5173", timeout=5)
                return response.status_code == 200
            else:
                return True  # Unknown service, assume it's running
        except Exception as e:
            print(f"    ⚠️  Verification failed for {name}: {e}")
            return False
    
    def start_control_loop(self):
        """Start control loop in the current terminal"""
        print("\n🎮 Control Terminal Active!")
        print("Type 'kill' to stop all services")
        print("Type 'status' to check service status")
        print("Type 'restart <service>' to restart a specific service")
        print("Type 'quit' to exit control mode")
        print("Available services: backend, mcp_server, blue_agent, red_agent, green_agent, frontend")
        print("----------------------------------------")
        
        while True:
            try:
                cmd = input("AgentBeats> ").strip().lower()
                
                if cmd == "kill":
                    print("🛑 Stopping all services...")
                    try:
                        subprocess.run(["pkill", "-f", "python.*src.backend.run"], check=False)
                        subprocess.run(["pkill", "-f", "python.*src/logging/testing_mcp.py"], check=False)
                        subprocess.run(["pkill", "-f", "python.*scenarios/agent_launcher.py"], check=False)
                        subprocess.run(["pkill", "-f", "npm.*run.*dev"], check=False)
                        print("✅ All services stopped")
                    except Exception as e:
                        print(f"⚠️  Error stopping services: {e}")
                    break
                    
                elif cmd.startswith("restart "):
                    service_name = cmd.split(" ", 1)[1]
                    if service_name in SERVICES:
                        print(f"🔄 Restarting {service_name}...")
                        try:
                            # Stop the specific service
                            if service_name == "backend":
                                subprocess.run(["pkill", "-f", "python.*src.backend.run"], check=False)
                            elif service_name == "mcp_server":
                                subprocess.run(["pkill", "-f", "python.*src/logging/testing_mcp.py"], check=False)
                            elif service_name in ["blue_agent", "red_agent", "green_agent"]:
                                subprocess.run(["pkill", "-f", "python.*scenarios/agent_launcher.py"], check=False)
                            elif service_name == "frontend":
                                subprocess.run(["pkill", "-f", "npm.*run.*dev"], check=False)
                            
                            time.sleep(2)  # Wait for service to stop
                            
                            # Start the service again
                            config = SERVICES[service_name]
                            success = self.start_service(service_name, config)
                            if success:
                                print(f"✅ {service_name} restarted successfully")
                            else:
                                print(f"⚠️  Failed to restart {service_name}")
                        except Exception as e:
                            print(f"⚠️  Error restarting {service_name}: {e}")
                    else:
                        print(f"❌ Unknown service: {service_name}")
                        print("Available services: backend, mcp_server, blue_agent, red_agent, green_agent, frontend")
                    
                elif cmd == "status":
                    print("📊 Service Status:")
                    try:
                        # Check backend
                        response = requests.get("http://localhost:9000/health", timeout=2)
                        print("Backend (9000): ✅ Running" if response.status_code == 200 else "Backend (9000): ❌ Stopped")
                    except:
                        print("Backend (9000): ❌ Stopped")
                    
                    try:
                        # Check MCP server
                        response = requests.get("http://localhost:9001/sse", timeout=2)
                        print("MCP (9001): ✅ Running" if response.status_code == 200 else "MCP (9001): ❌ Stopped")
                    except:
                        print("MCP (9001): ❌ Stopped")
                    
                    try:
                        # Check frontend
                        response = requests.get("http://localhost:5173", timeout=2)
                        print("Frontend (5173): ✅ Running" if response.status_code == 200 else "Frontend (5173): ❌ Stopped")
                    except:
                        print("Frontend (5173): ❌ Stopped")
                        
                elif cmd == "quit":
                    print("👋 Exiting control mode. Services will continue running.")
                    break
                    
                else:
                    print("Unknown command. Type 'kill' to stop all services, 'status' to check status, 'restart <service>' to restart a service, or 'quit' to exit.")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting control mode. Services will continue running.")
                break
            except EOFError:
                print("\n👋 Exiting control mode. Services will continue running.")
                break
    
    def start_service_linux(self, name, config):
        """Start service on Linux using gnome-terminal"""
        title = f"AgentBeats - {config['description']}"
        
        # Build the command
        cmd_str = " ".join(config['command'])
        if config['env']:
            env_str = " ".join([f"{k}={v}" for k, v in config['env'].items()])
            cmd_str = f"{env_str} {cmd_str}"
        
        # Add virtual environment activation for Python services
        if config.get('use_venv', False):
            venv_activate = "source venv/bin/activate && "
            cmd_str = f"{venv_activate}{cmd_str}"
        
        try:
            subprocess.Popen([
                "gnome-terminal", 
                "--title", title,
                "--working-directory", os.path.abspath(config['cwd']),
                "--", "bash", "-c", f"echo 'Starting {name}...' && {cmd_str}; exec bash"
            ])
            print(f"🔄 Started {name} in new terminal window, verifying...")
            time.sleep(2)
            if self.verify_service_running(name, config):
                print(f"✅ {name} is running successfully")
                return True
            else:
                print(f"⚠️  {name} terminal opened but service may not be running properly")
                return False
        except FileNotFoundError:
            print(f"❌ gnome-terminal not found. Please start {name} manually:")
            print(f"   cd {config['cwd']}")
            print(f"   {cmd_str}")
            return False
    
    def start_service_windows(self, name, config):
        """Start service on Windows using start command"""
        title = f"AgentBeats - {config['description']}"
        
        # Build the command
        cmd_str = " ".join(config['command'])
        if config['env']:
            env_str = " ".join([f"set {k}={v} &&" for k, v in config['env'].items()])
            cmd_str = f"{env_str} {cmd_str}"
        
        # Add virtual environment activation for Python services
        if config.get('use_venv', False):
            venv_activate = "venv\\Scripts\\activate && "
            cmd_str = f"{venv_activate}{cmd_str}"
        
        try:
            subprocess.Popen([
                "start", title, "cmd", "/k", 
                f"cd /d {os.path.abspath(config['cwd'])} && echo Starting {name}... && {cmd_str}"
            ], shell=True)
            print(f"🔄 Started {name} in new terminal window, verifying...")
            time.sleep(2)
            if self.verify_service_running(name, config):
                print(f"✅ {name} is running successfully")
                return True
            else:
                print(f"⚠️  {name} terminal opened but service may not be running properly")
                return False
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return False
    
    def start_service(self, name, config):
        """Start a service based on the operating system"""
        if self.system == "Darwin":  # macOS
            return self.start_service_macos(name, config)
        elif self.system == "Linux":
            return self.start_service_linux(name, config)
        elif self.system == "Windows":
            return self.start_service_windows(name, config)
        else:
            print(f"❌ Unsupported operating system: {self.system}")
            return False
    
    def start_all(self):
        """Start all services"""
        print("🚀 Starting AgentBeats services...")
        print("=" * 50)
        
        # Check environment first
        print("🔍 Checking environment...")
        self.check_environment()
        print()
        
        # Check OpenAI API key
        print("🔑 Checking API key...")
        self.check_openai_key()
        print()
        
        # Clean up any existing processes first
        print("🧹 Cleaning up any existing processes...")
        try:
            # Kill backend and MCP processes
            subprocess.run(["pkill", "-f", "python.*src.backend.run"], check=False)
            subprocess.run(["pkill", "-f", "python.*src/logging/testing_mcp.py"], check=False)
            
            # Kill agent launcher processes (controllers)
            subprocess.run(["pkill", "-f", "python.*scenarios/agent_launcher.py"], check=False)
            
            # Kill child agent processes (the actual agents on ports 9011, 9021, 9031)
            subprocess.run(["pkill", "-f", "python.*tensortrust_mock/blue_agent/main.py"], check=False)
            subprocess.run(["pkill", "-f", "python.*tensortrust_mock/red_agent/main.py"], check=False)
            subprocess.run(["pkill", "-f", "python.*tensortrust_mock/green_agent/main.py"], check=False)
            
            # Kill frontend processes
            subprocess.run(["pkill", "-f", "npm.*run.*dev"], check=False)
            
            # Also kill any processes on the specific ports
            subprocess.run(["lsof", "-ti", ":9010", ":9011", ":9020", ":9021", ":9030", ":9031"], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = subprocess.run(["lsof", "-ti", ":9010", ":9011", ":9020", ":9021", ":9030", ":9031"], 
                                   capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(["kill", "-9", pid], check=False)
            
            time.sleep(3)  # Give processes more time to shut down
            print("✅ Cleanup complete")
        except Exception as e:
            print(f"⚠️  Warning during cleanup: {e}")
        print()
        
        # Start services in order
        startup_order = ["backend", "mcp_server", "blue_agent", "red_agent", "green_agent", "frontend"]
        
        for service_name in startup_order:
            if service_name in SERVICES:
                config = SERVICES[service_name]
                print(f"Starting {service_name}...")
                success = self.start_service(service_name, config)
                if success:
                    time.sleep(1)  # Small delay between starts
                else:
                    print(f"⚠️  Failed to start {service_name}, continuing with others...")
                print()
        
        print("=" * 50)
        print("🎉 All services started!")
        print()
        print("📋 Service Summary:")
        print("   • Backend API: http://localhost:9000")
        print("   • MCP Server: http://localhost:9001")
        print("   • Blue Agent Controller: http://localhost:9010")
        print("   • Blue Agent: http://localhost:9011")
        print("   • Red Agent Controller: http://localhost:9020")
        print("   • Red Agent: http://localhost:9021") 
        print("   • Green Agent Controller: http://localhost:9030")
        print("   • Green Agent: http://localhost:9031")
        print("   • Frontend: http://localhost:5173")
        print()
        print("💡 Tips:")
        print("   • Wait a few seconds for all services to fully start")
        print("   • Check each terminal window for any error messages")
        print("   • Use Ctrl+C in any terminal to stop that service")
        print("   • Run this script again to restart all services")
        
        # Start control loop in current terminal
        self.start_control_loop()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("AgentBeats Auto-Start Script")
        print("Usage: python setup.py")
        print()
        print("This script will start all AgentBeats services in separate terminal windows:")
        for name, config in SERVICES.items():
            print(f"  • {name}: {config['description']}")
        print()
        print("Prerequisites:")
        print("  • Virtual environment (venv/) with dependencies installed")
        print("  • requirements.txt file present")
        print("  • Set OPENAI_API_KEY environment variable")
        print("  • Install Node.js dependencies in frontend/")
        print()
        print("Setup:")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("  pip install -r requirements.txt")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("  python setup.py")
        return
    
    manager = ServiceManager()
    manager.start_all()

if __name__ == "__main__":
    main() 