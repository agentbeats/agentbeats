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
import requests
import json
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
    
    def __init__(self, config: Dict[str, Any], scenario_dir: Path, task_index: int = None):
        self.card = config["card"]
        if "name" in config:
            self.name = config["name"]
        else:
            # read from card
            card_content = toml.load(scenario_dir / self.card)
            self.name = card_content.get("name", "Unnamed Agent")
            
        self.scenario_dir = scenario_dir
        self.task_index = task_index
        
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
        self.backend = config.get("backend") # warning: these can be None
        self.model_type = config.get("model_type")
        self.model_name = config.get("model_name")
        self.tools = config.get("tools", [])
        self.mcp_servers = config.get("mcp_servers", [])
        
        # New fields for API integration
        self.is_green = config.get("is_green", False)
        self.participant_requirements = config.get("participant_requirements", [])
        
        # Validate participant_requirements format if this is a green agent
        if self.is_green and self.participant_requirements:
            for req in self.participant_requirements:
                if not isinstance(req, dict):
                    raise ValueError(f"participant_requirements must be a list of dict for green agent {self.name}")
                required_fields = ["role", "name", "required", "participant_agent"]
                for field in required_fields:
                    if field not in req:
                        raise ValueError(f"participant_requirements item missing {field} for green agent {self.name}")
                if req["role"] not in ["blue_agent", "red_agent"]:
                    raise ValueError(f"role must be 'blue_agent' or 'red_agent' for green agent {self.name}")
                if not isinstance(req["required"], bool):
                    raise ValueError(f"required must be boolean for green agent {self.name}")
    
    def get_command(self,) -> str:
        """Generate the agentbeats run command for this agent"""
        # Use override backend if provided, otherwise use configured backend
        system = platform.system()

        if system == "Linux":
            env_append = ""
            if self.model_type == "openai":
                OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
                if not OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is not set")
                env_append = f"export OPENAI_API_KEY='{OPENAI_API_KEY}';"
            elif self.model_type == "openrouter":
                OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
                if not OPENROUTER_API_KEY:
                    raise ValueError("OPENROUTER_API_KEY is not set")
                env_append = f"export OPENROUTER_API_KEY='{OPENROUTER_API_KEY}';"
        
        
        cmd_parts = [
            "agentbeats", "run", self.card,
            "--launcher_host", self.launcher_host,
            "--launcher_port", str(self.launcher_port),
            "--agent_host", self.agent_host,
            "--agent_port", str(self.agent_port)
        ]

        if system == "Linux":
            # If running on Linux, prepend environment variables
            cmd_parts.insert(0, env_append)
        
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
    
    def __init__(self, scenario_root: Path, project_dir: Path = None):
        # Scenario root, e.g. "scenarios/tensortrust"
        self.scenario_root = Path(scenario_root)
        self.project_dir = Path(project_dir)
        
        # These will be loaded by `load_scenario_toml()`
        self.config: Dict[str, Any] = {}  
        self.services: List[ScenarioService] = []
        self.agents: List[ScenarioAgent] = []
        self.load_scenario_toml()

        # List to hold background processes
        self.processes: List[subprocess.Popen] = []
        
    def load_scenario_toml(self) -> None:
        """Load scenario configuration from scenario.toml"""
        scenario_file = self.scenario_root / "scenario.toml"
        
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_file}")
        
        with open(scenario_file, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        self.config = config
        
        # Load services
        self.services = []
        for service_config in config.get("services", []):
            service = ScenarioService(service_config, self.scenario_root)
            self.services.append(service)
        
        # Load agents to start
        self.agents = []
        for agent_config in config.get("agents", []):
            agent = ScenarioAgent(agent_config, self.scenario_root)
            self.agents.append(agent)

        # Load agents to register
        self.agents_to_register = []
        for agent_config in config.get("agents", []):
            if num_tasks := agent_config.get("num_tasks", None):
                for i in range(num_tasks):
                    agent = ScenarioAgent(
                        agent_config, self.scenario_root, task_index=i + 1
                    )
                    self.agents_to_register.append(agent)
            else:
                agent = ScenarioAgent(agent_config, self.scenario_root)
                self.agents_to_register.append(agent)
        
        print("===Agents to start===")
        for agent in self.agents:
            print(f"Agent {agent.name} task index: {agent.task_index}")

        print("===Agents to register===")
        for agent in self.agents_to_register:
            print(f"Agent {agent.name} task index: {agent.task_index}")

    
    def load_scenario(self, mode: str = None):
        """Start all components of a scenario"""
        scenario_name = self.config["scenario"]["name"] # Must provide a name in scenario.toml
        launch_config = self.config.get("launch", {})   # Optional launch configuration

        print(f"Starting scenario: {scenario_name}")
        
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
                self._start_agents_tmux(self.config)
            elif mode == "separate":
                self._start_agents_terminals()
            elif mode == "current":
                self._start_agents_background()
            else:
                raise ValueError(f"Unknown launch mode: {mode}")
    
    def _start_agents_tmux(self, config: Dict[str, Any]):
        """Start agents in tmux, each agent in a separate window of the same session"""
        if not shutil.which("tmux"):
            print("❌ tmux is not installed. Falling back to separate terminals.")
            self._start_agents_terminals()
            return

        launch_config = self.config.get("launch", {})
        session_name = launch_config.get("tmux_session_name", f"agentbeats-{self.config['scenario']['name']}")

        # Kill existing session if it exists
        subprocess.run(['tmux', 'kill-session', '-t', session_name], 
                      capture_output=True, check=False)

        # Create new session with first agent in first window
        first_agent = self.agents[0]
        cmd = f"cd '{first_agent.scenario_dir}' && {first_agent.get_command()}"
        subprocess.run([
            'tmux', 'new-session', '-d', '-s', session_name,
            '-n', first_agent.name,
            'bash', '-c', cmd
        ], check=True, env=os.environ.copy())

        # Create a new window for each subsequent agent
        for agent in self.agents[1:]:
            cmd = f"cd '{agent.scenario_dir}' && {agent.get_command()}"
            subprocess.run([
                'tmux', 'new-window', '-t', session_name,
                '-n', agent.name,
                'bash', '-c', cmd
            ], check=True, env=os.environ.copy())

        print(f"✅ Tmux session '{session_name}' created!")
        print(f"Each agent is running in a separate window of the session.")
        print(f"To attach: tmux attach -t {session_name}")
        print(f"To stop: tmux kill-session -t {session_name}")
    
    def _start_agents_terminals(self,):
        """Start agents in separate terminal windows"""
        system = platform.system()
        
        for agent in self.agents:
            print(f"Starting {agent.name}...")
            command = agent.get_command()
            
            if system == "Windows":
                full_cmd = f'start cmd /k "title {agent.name} && cd /d {agent.scenario_dir} && {command}"'
                subprocess.Popen(full_cmd, shell=True)
            elif system == "Darwin":  # macOS
                apple_script = f"""
                tell application "Terminal"
                    do script "source {self.project_dir}/venv/bin/activate && cd '{agent.scenario_dir}' && {command}"
                end tell
                """
                subprocess.Popen(["osascript", "-e", apple_script])
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
    
    def _start_agents_background(self,):
        """Start agents as background processes"""
        for agent in self.agents:
            print(f"Starting {agent.name}...")
            command = agent.get_command()
            
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
        for item in self.scenario_root.iterdir():
            if item.is_dir() and (item / "scenario.toml").exists():
                scenarios.append(item.name)
        return scenarios
    

    def register_agent_to_backend(self, agent: ScenarioAgent, backend_url: str = "http://localhost:9000") -> Optional[str]:
        """Register a single agent to the backend and return agent_id"""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Registering agent {agent.name} (attempt {attempt}/{max_retries})...")
                
                # Get agent card
                agent_url = f"http://{'localhost' if agent.agent_host == '0.0.0.0' else agent.agent_host}:{agent.agent_port}"
                launcher_url = f"http://{'localhost' if agent.launcher_host == '0.0.0.0' else agent.launcher_host}:{agent.launcher_port}"
                
                # Prepare registration data
                register_data = {
                    "alias": agent.name,
                    "agent_url": agent_url,
                    "launcher_url": launcher_url,
                    "is_green": agent.is_green
                }

                if agent.task_index:
                    print(f"Task index: {agent.task_index}")
                    register_data["task_config"] = str(agent.task_index)
                
                # Add participant_requirements for green agents
                if agent.is_green and agent.participant_requirements:
                    register_data["participant_requirements"] = agent.participant_requirements
                
                # Register agent
                response = requests.post(f"{backend_url}/agents", json=register_data, timeout=30)
                
                if response.status_code == 201:
                    result = response.json()
                    agent_id = result.get("agent_id")
                    print(f"✅ Registered agent {agent.name} with ID: {agent_id}")
                    return agent_id
                else:
                    print(f"⚠️ Failed to register agent {agent.name} (attempt {attempt}): {response.status_code} {response.text}")
                    if attempt < max_retries:
                        print(f"Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                    
            except Exception as e:
                print(f"⚠️ Error registering agent {agent.name} (attempt {attempt}): {str(e)}")
                if attempt < max_retries:
                    print(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
        
        print(f"❌ Failed to register agent {agent.name} after {max_retries} attempts")
        return None

    def register_agents_to_backend(
        self,
        backend_url: str = "http://localhost:9000",
    ):
        """
        Register all agents to the backend

        return agent_id_map, green_agent_id
        """
        # Register all agents
        agent_id_map = {}  # Maps agent name to registered agent_id
        green_agent_id = None

        for agent in self.agents_to_register:
            agent_id = self.register_agent_to_backend(agent, backend_url)
            if not agent_id:
                print(f"❌ Failed to register agent {agent.name}")
                return None, None
            agent_id_map[agent.name] = agent_id
            if agent.is_green:
                green_agent_id = agent_id

        return agent_id_map, green_agent_id


    def create_battle(self, green_agent_id: str, opponents: List[Dict[str, str]], backend_url: str = "http://localhost:9000") -> Optional[str]:
        """Create a battle and return battle_id"""
        try:
            battle_data = {
                "green_agent_id": green_agent_id,
                "opponents": opponents,
                "config": {}
            }
            
            response = requests.post(
                f"{backend_url}/battles",
                json=battle_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                battle_id = result.get("battle_id")
                print(f"✅ Created battle with ID: {battle_id}")
                return battle_id
            else:
                print(f"❌ Failed to create battle: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating battle: {str(e)}")
            return None
    
    def start_battle(self, backend_url: str, frontend_url: str) -> Optional[str]:
        """Load scenario, register agents, create battle, and return frontend URL"""
        print(f"Starting battle for scenario: {self.config['scenario']['name']}")
        
        # Find green agent
        green_agent = None
        for agent in self.agents:
            if agent.is_green:
                green_agent = agent
                break
        
        if not green_agent:
            print("❌ No green agent found in scenario")
            return None
        
        print(f"Found green agent: {green_agent.name}")

        # Register all agents
        agent_id_map, green_agent_id = self.register_agents_to_backend(
            backend_url
        )
        if not agent_id_map or not green_agent_id:
            print("❌ Failed to register agents")
            return None

        # Build opponents list based on participant_requirements
        opponents = []
        for req in green_agent.participant_requirements:
            participant_agent_name = req["participant_agent"]
            if participant_agent_name not in agent_id_map:
                print(
                    f"❌ Required participant agent {participant_agent_name} not found in scenario"
                )
                return None

            opponents.append(
                {
                    "name": req["name"],
                    "agent_id": agent_id_map[participant_agent_name],
                    "role": req["role"],
                }
            )

        print(f"Prepared {len(opponents)} opponents for battle")

        # Create battle
        battle_id = self.create_battle(green_agent_id, opponents, backend_url)
        if not battle_id:
            return None

        # Generate frontend URL
        battle_url = f"{frontend_url}/battles/{battle_id}"
        print(f"🎯 Battle URL: {battle_url}")

        return battle_url