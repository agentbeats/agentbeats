#!/usr/bin/env python3
"""
AgentBeats CTF Password Brute Force Demo
Simple script to launch the CTF challenge with green and red agents
"""

import os
import sys
import platform
import subprocess
import threading
import time
import argparse
import asyncio
from pathlib import Path

# Import SDK utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from agentbeats.utils.environment import setup_container, cleanup_container

# =============================================================================
# Configuration Section
# =============================================================================

SCENARIO_NAME = "ctf_password_brute_force"

# Configure agent launch commands
AGENT_COMMANDS = [
    {
        "name": "Green Agent (Orchestrator)",
        "command": "agentbeats run agents/green_agent/agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9010 --backend http://localhost:9000 --tool agents/green_agent/tools.py"
    },
    {
        "name": "Red Agent 1 (Competitor)",
        "command": "agentbeats run agents/red_agent/agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9020 --backend http://localhost:9000 --tool agents/red_agent/tools.py"
    },
    {
        "name": "Red Agent 2 (Competitor)", 
        "command": "agentbeats run agents/red_agent_2/agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9030 --backend http://localhost:9000 --tool agents/red_agent_2/tools.py"
    }
]

# Docker setup configuration
DOCKER_CONFIG = {"docker_dir": "arena", "compose_file": "docker-compose.yml"}

# =============================================================================
# Implementation Section
# =============================================================================

class CTFLauncher:
    def __init__(self):
        self.processes = []
        self.scenario_dir = Path(__file__).parent
        
    async def setup_docker(self):
        """Set up the Docker environment"""
        print("Setting up Docker environment...")
        
        docker_dir = self.scenario_dir / "docker"
        if not docker_dir.exists():
            print(f"Error: Docker directory not found at {docker_dir}")
            return False
        
        try:
            # Clean up any conflicting containers first
            print("🧹 Checking for conflicting containers...")
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                containers_to_stop = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) == 2:
                            container_name = parts[0]
                            ports = parts[1]
                            if ":2222->" in ports or "0.0.0.0:2222->" in ports:
                                containers_to_stop.append(container_name)
                                print(f"⚠️ Found container '{container_name}' using port 2222")
                
                # Stop conflicting containers
                for container_name in containers_to_stop:
                    print(f"🛑 Stopping container: {container_name}")
                    subprocess.run(["docker", "stop", container_name], capture_output=True)
                    print(f"✅ Stopped container: {container_name}")
                
                if containers_to_stop:
                    print("⏳ Waiting for ports to be released...")
                    time.sleep(3)
            
            # Use SDK utility to start Docker containers
            result = await setup_container(DOCKER_CONFIG)
            
            if result:
                print("✅ Docker environment setup completed successfully")
                print("   - SSH access available on localhost:2222")
                print("   - Container: ctf-password-brute-force")
                return True
            else:
                print(f"❌ Failed to setup Docker environment")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up Docker environment: {str(e)}")
            return False
    
    def cleanup_docker(self):
        """Clean up the Docker environment"""
        print("Cleaning up Docker environment...")
        
        docker_dir = self.scenario_dir / "arena"
        if not docker_dir.exists():
            print(f"Warning: Arena directory not found at {docker_dir}")
            return
        
        try:
            # Stop and remove Docker containers
            result = subprocess.run(
                ["docker-compose", "down", "--volumes", "--remove-orphans"],
                cwd=docker_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Docker environment cleanup completed")
            else:
                print(f"⚠️ Docker cleanup had issues: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ Error during Docker cleanup: {str(e)}")
    
    def start_agent_in_terminal(self, agent_config):
        """Start agent in a separate terminal window"""
        name = agent_config["name"]
        command = agent_config["command"]
        
        print(f"Starting {name}...")
        
        system = platform.system()
        
        if system == "Windows":
            # Windows command
            full_cmd = f'start cmd /k "title {name} && {command}"'
            subprocess.Popen(full_cmd, shell=True, cwd=self.scenario_dir)
            
        elif system == "Darwin":  # macOS
            # macOS command
            apple_script = f'''
            tell application "Terminal"
                do script "cd '{self.scenario_dir}' && {command}"
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
            
            full_cmd = f'{command}; exec bash'
            
            terminal_opened = False
            for term_cmd in terminal_cmds:
                try:
                    subprocess.Popen(term_cmd + [full_cmd], cwd=self.scenario_dir)
                    terminal_opened = True
                    break
                except FileNotFoundError:
                    continue
            
            if not terminal_opened:
                print(f"Warning: Could not open terminal window for {name}. Please run manually: {command}")
    
    def start_agent_in_current_terminal(self, agent_config):
        """Start agent in current terminal (background process)"""
        name = agent_config["name"]
        command = agent_config["command"]
        
        print(f"Starting {name}...")
        
        # Split command string into list
        cmd_parts = command.split()
        
        process = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=self.scenario_dir,
            shell=True
        )
        
        self.processes.append((name, process))
        
        # Create thread to handle output
        def handle_output(agent_name, proc):
            while True:
                output = proc.stdout.readline()
                if output == '' and proc.poll() is not None:
                    break
                if output:
                    print(f"[{agent_name}] {output.strip()}")
        
        thread = threading.Thread(target=handle_output, args=(name, process))
        thread.daemon = True
        thread.start()
    
    async def start_all_agents(self, separate_terminals=True, selected_agents=None, setup_docker=True):
        """Start all configured agents"""
        
        # Set up Docker first if requested
        if setup_docker:
            if not await self.setup_docker():
                print("❌ Failed to setup Docker. Please check Docker and try again.")
                return
            print("Waiting 10 seconds for Docker to be ready...")
            time.sleep(10)
        
        # Filter agents to start
        agents_to_start = AGENT_COMMANDS
        if selected_agents:
            agents_to_start = [agent for i, agent in enumerate(AGENT_COMMANDS) 
                             if str(i) in selected_agents or agent["name"].lower() in [s.lower() for s in selected_agents]]
        
        print(f"Starting {len(agents_to_start)} agents...")
        
        # Start agents
        for agent_config in agents_to_start:
            if separate_terminals:
                self.start_agent_in_terminal(agent_config)
            else:
                self.start_agent_in_current_terminal(agent_config)
            time.sleep(2)  # Small delay between starts
        
        print("✅ All agents started!")
        print("\n📋 Next steps:")
        print("1. Green Agent: Run 'setup_ctf_environment()' to set up the challenge")
        print("2. Green Agent: Run 'start_competition(\"red_agent_1,red_agent_2\")' to begin")
        print("3. Red Agents: Will receive challenge info and start brute forcing")
        print("4. First agent to find the flag wins!")
        
        # Keep the main process running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down agents...")
            self.cleanup()
    
    def cleanup(self):
        """Clean up all processes and Docker environment"""
        print("Cleaning up...")
        
        # Stop all agent processes
        for name, process in self.processes:
            try:
                process.terminate()
                print(f"Stopped {name}")
            except:
                pass
        
        # Clean up Docker
        self.cleanup_docker()
        
        print("✅ Cleanup completed")
    
    def show_commands(self):
        """Show available commands"""
        print("\n📋 Available Commands:")
        print("  start                    - Start all agents in separate terminals")
        print("  start --current          - Start all agents in current terminal")
        print("  start --agents 0,1       - Start specific agents (0=Green, 1=Red1, 2=Red2)")
        print("  cleanup                  - Clean up Docker environment")
        print("  help                     - Show this help message")
        print("\n🎯 CTF Challenge Flow:")
        print("1. Green Agent sets up Docker environment and generates flag")
        print("2. Green Agent starts competition with red agents")
        print("3. Red agents receive user persona and SSH credentials")
        print("4. Red agents brute force passwords to find the flag")
        print("5. First agent to submit correct flag wins!")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="CTF Password Brute Force Demo")
    parser.add_argument("command", nargs="?", default="start", 
                       choices=["start", "cleanup", "help"],
                       help="Command to execute")
    parser.add_argument("--current", action="store_true",
                       help="Start agents in current terminal instead of separate windows")
    parser.add_argument("--agents", type=str,
                       help="Comma-separated list of agent indices to start (0=Green, 1=Red1, 2=Red2)")
    parser.add_argument("--no-docker", action="store_true",
                       help="Skip Docker setup (use existing environment)")
    
    args = parser.parse_args()
    
    launcher = CTFLauncher()
    
    if args.command == "start":
        selected_agents = args.agents.split(",") if args.agents else None
        asyncio.run(launcher.start_all_agents(
            separate_terminals=not args.current,
            selected_agents=selected_agents,
            setup_docker=not args.no_docker
        ))
    elif args.command == "cleanup":
        launcher.cleanup()
    elif args.command == "help":
        launcher.show_commands()

if __name__ == "__main__":
    main() 