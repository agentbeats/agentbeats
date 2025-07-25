#!/usr/bin/env python3
"""
AgentBeats Scenario Agent Launcher
Simple script to launch multiple agents for a scenario
"""

import os
import sys
import platform
import subprocess
import threading
import time
import argparse
from pathlib import Path

# =============================================================================
# Configuration Section - Modify your scenario commands here
# =============================================================================

SCENARIO_NAME = "tensortrust"

# Configure your agent launch commands here
AGENT_COMMANDS = [
    {
        "name": "Blue Agent",
        "command": "agentbeats run blue_agent/blue_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9010 --backend http://localhost:9000"
    },
    {
        "name": "Red Agent", 
        "command": "agentbeats run red_agent/red_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9020 --backend http://localhost:9000"
    },
    {
        "name": "Green Agent",
        "command": "agentbeats run green_agent/green_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9030 --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool green_agent/tools.py"
    }
]

# =============================================================================
# Implementation Section - No need to modify
# =============================================================================

class AgentLauncher:
    def __init__(self):
        self.processes = []
        self.scenario_dir = Path(__file__).parent
        
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
    
    def start_all_agents(self, separate_terminals=True, selected_agents=None):
        """Start all configured agents"""
        
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
            
        else:
            print(f"Starting {len(agents_to_start)} agents in current terminal...")
            try:
                for agent in agents_to_start:
                    self.start_agent_in_current_terminal(agent)
                
                print(f"\nAll agents started! Press Ctrl+C to stop all agents.")
                
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
        
        for i, agent in enumerate(AGENT_COMMANDS):
            print(f"\n{i+1}. {agent['name']}:")
            print(f"   {agent['command']}")
        
        print(f"\nNote: Please run these commands from the {self.scenario_dir} directory")


def main():
    parser = argparse.ArgumentParser(
        description=f'Launch {SCENARIO_NAME} scenario agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_agents.py                    # Start all agents in separate terminals  
  python start_agents.py --current         # Start all agents in current terminal
  python start_agents.py --show            # Show commands without running
  python start_agents.py --agents 0 1      # Start only agent 0 and 1
        """
    )
    
    parser.add_argument('--current', action='store_true',
                       help='Start agents in current terminal instead of separate windows')
    parser.add_argument('--agents', nargs='+',
                       help='Start specific agents (use index numbers or names)')
    parser.add_argument('--show', action='store_true',
                       help='Show agent commands without running them')
    
    args = parser.parse_args()
    
    launcher = AgentLauncher()
    
    # Show commands only
    if args.show:
        launcher.show_commands()
        return
    
    # Start agents
    launcher.start_all_agents(
        separate_terminals=not args.current,
        selected_agents=args.agents
    )


if __name__ == "__main__":
    main()
