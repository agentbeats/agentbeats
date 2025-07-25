# -*- coding: utf-8 -*-
"""
Scenario Manager for AgentBeats
Handles loading and launching scenarios defined in scenario.toml files
"""

import os
import sys
import time
import subprocess
import threading
import platform
import shutil
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Any
import toml


class ScenarioService:
    """Service that needs to be started for a scenario"""
    
    def __init__(self, config: Dict[str, Any], scenario_dir: Path):
        self.name = config["name"]
        self.type = config["type"]
        self.scenario_dir = scenario_dir
        self.working_dir = scenario_dir / config.get("working_dir", ".")
        self.startup_delay = config.get("startup_delay", 0)
        self.health_check = config.get("health_check")
        self.process = None
        
        if self.type == "docker_compose":
            self.compose_file = config.get("compose_file", "docker-compose.yml")
        elif self.type == "command":
            self.command = config["command"]
        else:
            raise ValueError(f"Unknown service type: {self.type} for service {self.name}")
    
    def start(self):
        """Start the service"""
        print(f"Starting service: {self.name}")
        
        if self.type == "docker_compose":
            self._start_docker_compose()
        elif self.type == "command":
            self._start_command()
        
        if self.startup_delay > 0:
            print(f"Waiting {self.startup_delay}s for {self.name} to start...")
            time.sleep(self.startup_delay)
    
    def _start_docker_compose(self):
        """Start Docker Compose service"""
        cmd = ["docker-compose", "-f", self.compose_file, "up", "-d"]
        self.process = subprocess.Popen(
            cmd,
            cwd=self.working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = self.process.communicate()
        
        if self.process.returncode != 0:
            raise RuntimeError(f"Failed to start {self.name}: {stderr.decode()}")
        
        print(f"Docker Compose service {self.name} started")
    
    def _start_command(self):
        """Start command-based service"""
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            cwd=self.working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Command service {self.name} started (PID: {self.process.pid})")
    
    def stop(self):
        """Stop the service"""
        if self.type == "docker_compose":
            cmd = ["docker-compose", "-f", self.compose_file, "down"]
            subprocess.run(cmd, cwd=self.working_dir)
            print(f"Docker Compose service {self.name} stopped")
        elif self.type == "command" and self.process:
            self.process.terminate()
            self.process.wait()
            print(f"Command service {self.name} stopped")
    
    def is_healthy(self) -> bool:
        """Check if service is healthy"""
        if not self.health_check:
            return True
        
        try:
            with urllib.request.urlopen(self.health_check, timeout=5) as response: #TODO: haven't tested this
                return response.status == 200
        except:
            return False


class ScenarioAgent:
    """Represents an agent configuration for a scenario"""
    
    def __init__(self, config: Dict[str, Any], scenario_dir: Path):
        self.card = config["card"]
        if "name" in config:
            self.name = config["name"]
        else:
            # read from card
            card_content = toml.load(scenario_dir / self.card)
            self.name = card_content.get("name", "Unnamed Agent")
            
        self.scenario_dir = scenario_dir
        
        # Agent configuration
        # Required fields
        if "launcher_host" not in config:
            raise ValueError(f"launcher_host is required for agent {self.name}")
        if "launcher_port" not in config:
            raise ValueError(f"launcher_port is required for agent {self.name}")
        if "agent_host" not in config:
            raise ValueError(f"agent_host is required for agent {self.name}")
        if "agent_port" not in config:
            raise ValueError(f"agent_port is required for agent {self.name}")
        
        self.launcher_host = config["launcher_host"]
        self.launcher_port = config["launcher_port"]
        self.agent_host = config["agent_host"]
        self.agent_port = config["agent_port"]
        
        # Optional fields
        self.backend = config.get("backend", "http://localhost:9000")
        self.model_type = config.get("model_type")
        self.model_name = config.get("model_name")
        self.tools = config.get("tools", [])
        self.mcp_servers = config.get("mcp_servers", [])
    
    def get_command(self, backend_override: str = None) -> str:
        """Generate the agentbeats run command for this agent"""
        # Use override backend if provided, otherwise use configured backend
        backend = backend_override if backend_override else self.backend
        
        cmd_parts = [
            "agentbeats", "run", self.card,
            "--launcher_host", self.launcher_host,
            "--launcher_port", str(self.launcher_port),
            "--agent_host", self.agent_host,
            "--agent_port", str(self.agent_port),
            "--backend", backend
        ]
        
        # Add model configuration only if specified
        if self.model_type:
            cmd_parts.extend(["--model_type", self.model_type])
        if self.model_name:
            cmd_parts.extend(["--model_name", self.model_name])
        
        # Add tools
        for tool in self.tools:
            cmd_parts.extend(["--tool", tool])
        
        # Add MCP servers
        for mcp in self.mcp_servers:
            cmd_parts.extend(["--mcp", mcp])
        
        return " ".join(cmd_parts)


class ScenarioManager:
    """Manages scenario loading and execution"""
    
    def __init__(self, scenarios_root: Path = None):
        if scenarios_root is None:
            # Default to scenarios directory relative to this file
            current_file = Path(__file__).resolve()
            self.scenarios_root = current_file.parent.parent.parent.parent.parent / "scenarios"
        else:
            self.scenarios_root = Path(scenarios_root)
        
        self.services: List[ScenarioService] = []
        self.agents: List[ScenarioAgent] = []
        self.processes: List[subprocess.Popen] = []
    
    def load_scenario_toml(self, scenario_name: str) -> Dict[str, Any]:
        """Load scenario configuration from scenario.toml"""
        scenario_dir = self.scenarios_root / scenario_name
        scenario_file = scenario_dir / "scenario.toml"
        
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_file}")
        
        with open(scenario_file, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        
        # Load services
        self.services = []
        for service_config in config.get("services", []):
            service = ScenarioService(service_config, scenario_dir)
            self.services.append(service)
        
        # Load agents
        self.agents = []
        for agent_config in config.get("agents", []):
            agent = ScenarioAgent(agent_config, scenario_dir)
            self.agents.append(agent)
        
        return config
    
    def load_scenario(self, scenario_name: str, mode: str = None, backend_override: str = None):
        """Start all components of a scenario"""
        print(f"Starting scenario: {scenario_name}")
        
        if backend_override:
            print(f"Using backend override: {backend_override}")
        
        config = self.load_scenario_toml(scenario_name)
        launch_config = config.get("launch", {})
        
        startup_interval = launch_config.get("startup_interval", 1)
        wait_for_services = launch_config.get("wait_for_services", True)
        
        if self.services:
            print(f"\nStarting {len(self.services)} services...")
            for service in self.services:
                service.start()
                time.sleep(startup_interval)
            
            if wait_for_services:
                print("\nChecking service health...")
                for service in self.services:
                    if service.health_check:
                        max_retries = 30
                        for i in range(max_retries):
                            if service.is_healthy():
                                print(f"✓ {service.name} is healthy")
                                break
                            print(f"Waiting for {service.name} to be healthy... ({i+1}/{max_retries})")
                            time.sleep(2)
                        else:
                            print(f"⚠️  {service.name} health check failed, continuing anyway...")

        if mode is None or mode == "":
            mode = launch_config.get("mode", "tmux")

        if self.agents:
            print(f"\nStarting {len(self.agents)} agents...")
            
            if mode == "tmux":
                self._start_agents_tmux(config, backend_override)
            elif mode == "separate":
                self._start_agents_terminals(backend_override)
            elif mode == "current":
                self._start_agents_background(backend_override)
            else:
                raise ValueError(f"Unknown launch mode: {mode}")
    
    def _start_agents_tmux(self, config: Dict[str, Any], backend_override: str = None):
        """Start agents in tmux panes"""
        if not shutil.which("tmux"):
            print("❌ tmux is not installed. Falling back to separate terminals.")
            self._start_agents_terminals(backend_override)
            return
        
        launch_config = config.get("launch", {})
        session_name = launch_config.get("tmux_session_name", f"agentbeats-{config['scenario']['name']}")
        
        # Kill existing session if it exists
        subprocess.run(['tmux', 'kill-session', '-t', session_name], 
                      capture_output=True, check=False)
        
        # Create new session with first agent
        first_agent = self.agents[0]
        cmd = f"cd '{first_agent.scenario_dir}' && {first_agent.get_command(backend_override)}"
        
        subprocess.run([
            'tmux', 'new-session', '-d', '-s', session_name,
            '-x', '120', '-y', '30',
            'bash', '-c', cmd
        ], check=True)
        
        subprocess.run([
            'tmux', 'rename-window', '-t', f"{session_name}:0", 
            first_agent.name
        ], check=True)
        for i, agent in enumerate(self.agents[1:], 1):
            cmd = f"cd '{agent.scenario_dir}' && {agent.get_command(backend_override)}"
            if i == 1:
                subprocess.run([
                    'tmux', 'split-window', '-t', session_name, '-h',
                    'bash', '-c', cmd
                ], check=True)
            else:
                subprocess.run([
                    'tmux', 'split-window', '-t', session_name, '-v',
                    'bash', '-c', cmd
                ], check=True)
            subprocess.run([
                'tmux', 'select-pane', '-t', session_name, '-T', agent.name
            ], check=True)
        
        subprocess.run([
            'tmux', 'set', '-t', session_name, 'pane-border-status', 'top'
        ], check=True)
        
        subprocess.run([
            'tmux', 'set', '-t', session_name, 'pane-border-format', 
            '#{pane_title}'
        ], check=True)
        
        subprocess.run([
            'tmux', 'select-layout', '-t', session_name, 'tiled'
        ], check=True)
        
        print(f"✅ Tmux session '{session_name}' created!")
        print(f"To attach: tmux attach -t {session_name}")
        print(f"To stop: tmux kill-session -t {session_name}")
    
    def _start_agents_terminals(self, backend_override: str = None):
        """Start agents in separate terminal windows"""
        system = platform.system()
        
        for agent in self.agents:
            print(f"Starting {agent.name}...")
            command = agent.get_command(backend_override)
            
            if system == "Windows":
                full_cmd = f'start cmd /k "title {agent.name} && cd /d {agent.scenario_dir} && {command}"'
                subprocess.Popen(full_cmd, shell=True)
            elif system == "Darwin":  # macOS
                apple_script = f'''
                tell application "Terminal"
                    do script "cd '{agent.scenario_dir}' && {command}"
                end tell
                '''
                subprocess.Popen(['osascript', '-e', apple_script])
            else:  # Linux
                terminal_cmds = [
                    ['gnome-terminal', '--', 'bash', '-c'],
                    ['xterm', '-e', 'bash', '-c'],
                    ['konsole', '-e', 'bash', '-c'],
                ]
                
                full_cmd = f'cd "{agent.scenario_dir}" && {command}; exec bash'
                
                for term_cmd in terminal_cmds:
                    try:
                        subprocess.Popen(term_cmd + [full_cmd])
                        break
                    except FileNotFoundError:
                        continue
            
            time.sleep(1)
        
        print("✅ All agents started in separate terminals!")
    
    def _start_agents_background(self, backend_override: str = None):
        """Start agents as background processes"""
        for agent in self.agents:
            print(f"Starting {agent.name}...")
            command = agent.get_command(backend_override)
            
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=agent.scenario_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            self.processes.append(process)
            
            # Create output handler thread
            def handle_output(agent_name, proc):
                while True:
                    output = proc.stdout.readline()
                    if output == '' and proc.poll() is not None:
                        break
                    if output:
                        print(f"[{agent_name}] {output.strip()}")
            
            thread = threading.Thread(target=handle_output, args=(agent.name, process))
            thread.daemon = True
            thread.start()
        
        print("✅ All agents started in background!")
        print("Press Ctrl+C to stop all agents")
        
        try:
            for process in self.processes:
                process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping all agents...")
            for process in self.processes:
                process.terminate()
                process.wait()
            print("✅ All agents stopped.")
    
    def stop_scenario(self, scenario_name: str):
        """Stop all components of a scenario"""
        print(f"Stopping scenario: {scenario_name}")
        
        # Stop services
        for service in self.services:
            service.stop()
        
        # Stop processes if running in background mode
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                process.wait()
        
        print("✅ Scenario stopped.")
    
    def list_scenarios(self) -> List[str]:
        """List all available scenarios"""
        scenarios = []
        for item in self.scenarios_root.iterdir():
            if item.is_dir() and (item / "scenario.toml").exists():
                scenarios.append(item.name)
        return scenarios


def main():
    """CLI entry point for scenario management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentBeats Scenario Manager")
    parser.add_argument("action", choices=["list", "start", "stop", "show"], 
                       help="Action to perform")
    parser.add_argument("scenario", nargs="?", help="Scenario name")
    parser.add_argument("--mode", choices=["tmux", "terminals", "background"], 
                       help="Launch mode")
    parser.add_argument("--backend", help="Override backend URL for all agents")
    
    args = parser.parse_args()
    
    manager = ScenarioManager()
    
    if args.action == "list":
        scenarios = manager.list_scenarios()
        print("Available scenarios:")
        for scenario in scenarios:
            print(f"  - {scenario}")
    
    elif args.action == "load":
        if not args.scenario:
            print("Error: scenario name required for load action")
            return
        manager.load_scenario(args.scenario, args.mode, args.backend)
    
    elif args.action == "stop":
        if not args.scenario:
            print("Error: scenario name required for stop action")
            return
        manager.stop_scenario(args.scenario)
    
    elif args.action == "show":
        if not args.scenario:
            print("Error: scenario name required for show action")
            return
        config = manager.load_scenario_toml(args.scenario)
        print(f"Scenario: {config['scenario']['name']}")
        print(f"Description: {config['scenario']['description']}")
        print(f"Services: {len(manager.services)}")
        print(f"Agents: {len(manager.agents)}")


if __name__ == "__main__":
    main()
