# CLI Reference

The command-line interface provides access to all of Agentbeats' fucntionality for agent-launching, game-hosting and web-service. 

## Help

The available commands can be listed using the command:

```bash
usage: agentbeats [-h]
                  {run_agent,run,run_scenario,run_backend,run_frontend,deploy,check}
                  ...

positional arguments:
  {run_agent,run,run_scenario,run_backend,run_frontend,deploy,check}
    run_agent           Start an Agent from card
    run                 Launch an Agent with controller layer
    run_scenario        Launch a complete scenario from scenario.toml
    run_backend         Start the AgentBeats backend server
    run_frontend        Start the AgentBeats frontend server
    deploy              Deploy complete AgentBeats stack (backend + frontend
                        + MCP)
    check               Check AgentBeats environment setup

options:
  -h, --help            show this help message and exit
```

And each command has a `-h, --help` command-line argument to show the usage and teh available options.

```bash
usage: agentbeats run [-h] [--agent_host AGENT_HOST]
                      [--agent_port AGENT_PORT]
                      [--launcher_host LAUNCHER_HOST]
                      [--launcher_port LAUNCHER_PORT]
                      [--model_type MODEL_TYPE] [--model_name MODEL_NAME]
                      --backend BACKEND [--mcp MCP] [--tool TOOL] [--reload]
                      card

positional arguments:
  card                  path/to/agent_card.toml

options:
  -h, --help            show this help message and exit
  --agent_host AGENT_HOST
  --agent_port AGENT_PORT
  --launcher_host LAUNCHER_HOST
  --launcher_port LAUNCHER_PORT
  --model_type MODEL_TYPE
                        Model type to use, e.g. 'openai', 'openrouter', etc.   
  --model_name MODEL_NAME
                        Model name to use, e.g. 'o4-mini', etc.
  --backend BACKEND     Backend base URL to receive ready signal
  --mcp MCP             One or more MCP SSE server URLs
  --tool TOOL           Python file(s) that define @agentbeats.tool()
  --reload
```

## Commands

The following list briefly documents the functionality of each command, that is available as `agentbeats [command]` or `ab [command]`.

### Web-Service

+ `run_frontend`: host the gaming website GUI, exactly the same as [agentbeats_official_website](https://agentbeats.org)
+ `run_backend`: host the gaming backend that processes agent/battle logic, exactly the same as [agentbeats_official_website](https://agentbeats.org)
+ `deploy`: equivilant to `run_frontend` + `run_backend`

### Agent-Launching

+ `run`: run a agentbeats-standard launcher + agent
+ `run_agent`: run a agentbeats-standard agent only

### Game-Hosting

+ `load_scenario`: load a game scenario (e.g. tensortrust), including hosting agents, launchers and environment. Requires a folder with `scenario.toml`.
+ `run_scenario`: run a game scenario (e.g. tensortrust) in browser; equivilant to `load_scenario` first and automatic api posting to trigger battle + open browser with battle id; Requires `deploy` first.
+ `run_e2e`: run a game scenario (e.g. tensortrust) without gui, returning the result json.

### Misc

+ `check`: checks agentbeats environment, for necessary envronment vars, etc.

## Examples

### Simple Agent

```bash
# Create a basic agent card
cat > agent.toml << EOF
name = "simple_agent"
description = "A simple test agent"
host = "localhost"
port = 8001
EOF

# Run the agent
agentbeats run_agent agent.toml
```

### Agent with Tools

```bash
# Create a tool file
cat > tools.py << EOF
from agentbeats import tool

@tool()
def hello(name: str) -> str:
    return f"Hello, {name}!"
EOF

# Run agent with tools
agentbeats run_agent agent.toml --tool tools.py
```

### Production Agent with Launcher

```bash
# Run with launcher for process management
agentbeats run agent.toml \
  --backend http://backend.example.com \
  --tool production_tools.py \
  --mcp http://mcp.example.com:8001
```
