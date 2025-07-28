#!/usr/bin/env python3
"""
AgentBeats Web Service Battle Royale Agent Launcher
Simple script to launch multiple agents for the battle royale scenario
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from agentbeats.utils.environment import setup_container, cleanup_container

# =============================================================================
# Configuration Section - Modify your scenario commands here
# =============================================================================

SCENARIO_NAME = "web_service_battle_royale"

# Configure your agent launch commands here
AGENT_COMMANDS = [
    {
        "name": "Green Agent (Monitor)",
        "command": "agentbeats run agents/green_agent/agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9010 --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool agents/green_agent/tools.py"
    },
    {
        "name": "Red Agent (Competitor)", 
        "command": "agentbeats run agents/red_agent/agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9020 --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool agents/red_agent/tools.py"
    }
]

# Arena setup configuration
ARENA_CONFIG = {"docker_dir": "arena", "compose_file": "docker-compose.yml"}

# =============================================================================
# Implementation Section - No need to modify
# =============================================================================

class AgentLauncher:
    def __init__(self):
        self.processes = []
        self.scenario_dir = Path(__file__).parent
        
    async def setup_arena(self):
        """Set up the battle arena Docker environment"""
        print("Setting up battle arena...")
        
        arena_dir = self.scenario_dir / "arena"
        if not arena_dir.exists():
            print(f"Error: Arena directory not found at {arena_dir}")
            return False
        
        try:
            # Use SDK utility to start Docker containers
            result = await setup_container(ARENA_CONFIG)
            
            if result:
                print("✅ Battle arena setup completed successfully")
                print("   - Docker containers started")
                print("   - SSH access available on localhost:2222")
                print("   - Web service monitoring on localhost:8081")
                return True
            else:
                print(f"❌ Failed to setup battle arena")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up battle arena: {str(e)}")
            return False
    
    def cleanup_arena(self):
        """Clean up the battle arena Docker environment"""
        print("Cleaning up battle arena...")
        
        arena_dir = self.scenario_dir / "arena"
        if not arena_dir.exists():
            print(f"Warning: Arena directory not found at {arena_dir}")
            return
        
        try:
            # Stop and remove Docker containers
            result = subprocess.run(
                ["docker-compose", "down", "--volumes", "--remove-orphans"],
                cwd=arena_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Battle arena cleanup completed")
            else:
                print(f"⚠️ Arena cleanup had issues: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ Error during arena cleanup: {str(e)}")
    
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
            shell=True  # Required shell=True on Windows
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
    
    async def start_all_agents(self, separate_terminals=True, selected_agents=None, setup_arena=True):
        """Start all configured agents"""
        
        # Set up arena first if requested
        if setup_arena:
            if not await self.setup_arena():
                print("❌ Failed to setup arena. Please check Docker and try again.")
                return
            print("Waiting 5 seconds for arena to be ready...")
            time.sleep(5)
        
        # Filter agents to start
        agents_to_start = AGENT_COMMANDS
        if selected_agents:
            agents_to_start = [agent for i, agent in enumerate(AGENT_COMMANDS) 
                             if str(i) in selected_agents or agent["name"].lower() in [s.lower() for s in selected_agents]]
        
        if separate_terminals:
            print(f"Starting {len(agents_to_start)} agents in separate terminal windows...")
            for agent in agents_to_start:
                self.start_agent_in_terminal(agent)
                time.sleep(1)  # Launch interval
            
            print(f"\nAll agents started in separate terminals!")
            print(f"\nCheck the newly opened terminal windows for agent status")
            print(f"\nBattle Royale Setup Complete:")
            print(f"  - Green Agent (Monitor): http://localhost:9010")
            print(f"  - Red Agent (Competitor): http://localhost:9020")
            print(f"  - Arena SSH: localhost:2222 (battle/battle123)")
            print(f"  - Web Service Monitor: http://localhost:8081")
            
        else:
            print(f"Starting {len(agents_to_start)} agents in current terminal...")
            try:
                for agent in agents_to_start:
                    self.start_agent_in_current_terminal(agent)
                
                print(f"\nAll agents started! Press Ctrl+C to stop all agents.")
                print(f"\nBattle Royale Setup Complete:")
                print(f"  - Green Agent (Monitor): http://localhost:9010")
                print(f"  - Red Agent (Competitor): http://localhost:9020")
                print(f"  - Arena SSH: localhost:2222 (battle/battle123)")
                print(f"  - Web Service Monitor: http://localhost:8081")
                
                for name, process in self.processes:
                    process.wait()
                    
            except KeyboardInterrupt:
                print("\n\nShutting down agents...")
                for name, process in self.processes:
                    print(f"Stopping {name}...")
                    process.terminate()
                    process.wait()
                print("All agents stopped.")
    
    def show_commands(self):
        """Display all agent commands"""
        print(f"\n{SCENARIO_NAME} Scenario Agent Commands:")
        print("=" * 60)
        
        print(f"\nArena Setup:")
        print(f"   Using agentbeats.utils.environment.setup_container")
        
        for i, agent in enumerate(AGENT_COMMANDS):
            print(f"\n{i+1}. {agent['name']}:")
            print(f"   {agent['command']}")
        
        print(f"\nNote: Please run these commands from the {self.scenario_dir} directory")
        print(f"\nBattle Royale Information:")
        print(f"  - The Green Agent monitors the battle and determines the winner")
        print(f"  - The Red Agent competes by creating a web service")
        print(f"  - Agents SSH into the arena container to compete")
        print(f"  - The battle runs for 50 seconds with monitoring every 5 seconds")


def main():
    parser = argparse.ArgumentParser(
        description=f'Launch {SCENARIO_NAME} scenario agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_agents.py                    # Start arena and all agents in separate terminals  
  python start_agents.py --current         # Start arena and all agents in current terminal
  python start_agents.py --show            # Show commands without running
  python start_agents.py --agents 0        # Start only the green agent (monitor)
  python start_agents.py --no-arena        # Start agents without arena setup
        """
    )
    
    parser.add_argument('--current', action='store_true',
                       help='Start agents in current terminal instead of separate windows')
    parser.add_argument('--agents', nargs='+',
                       help='Start specific agents (use index numbers or names)')
    parser.add_argument('--show', action='store_true',
                       help='Show agent commands without running them')
    parser.add_argument('--no-arena', action='store_true',
                       help='Skip arena setup (assumes arena is already running)')
    
    args = parser.parse_args()
    
    launcher = AgentLauncher()
    
    # Show commands only
    if args.show:
        launcher.show_commands()
        return
    
    # Start agents
    asyncio.run(launcher.start_all_agents(
        separate_terminals=not args.current,
        selected_agents=args.agents,
        setup_arena=not args.no_arena
    ))


if __name__ == "__main__":
    main()
