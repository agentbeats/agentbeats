# API Reference

Complete API documentation for the AgentBeats SDK.

## Core Classes

### BeatsAgent

Main agent class for creating and running agents.

```python
from agentbeats import BeatsAgent

agent = BeatsAgent(name: str)
```

#### Methods

- `load_agent_card(card_path: str)` - Load agent configuration from TOML file
- `add_mcp_server(url: str)` - Add MCP server to agent
- `run()` - Start the agent server
- `get_app()` - Get the FastAPI application instance
- `tool(name: str = None)` - Decorator to register functions as tools

#### Example

```python
agent = BeatsAgent("my_agent")

@agent.tool()
def my_tool():
    return "Hello from tool!"

agent.load_agent_card("agent.toml")
agent.run()
```

### BeatsAgentLauncher

Launcher for managing agent processes with restart capabilities.

```python
from agentbeats import BeatsAgentLauncher

launcher = BeatsAgentLauncher(
    agent_card: str,
    mcp_list: List[str],
    tool_list: List[str],
    backend_url: str,
    launcher_host: str = "0.0.0.0",
    launcher_port: int = 8000
)
```

#### Methods

- `run(reload: bool = False)` - Start the launcher server
- `shutdown()` - Clean shutdown of the launcher

## Utility Classes

### SSHClient

SSH client for remote command execution.

```python
from agentbeats.utils.commands import SSHClient

ssh = SSHClient(host: str, credentials: Dict[str, Any])
```

#### Methods

- `connect() -> bool` - Connect to SSH host
- `execute(command: str) -> str` - Execute command on remote host
- `disconnect()` - Close SSH connection

#### Example

```python
ssh = SSHClient("host.com", {
    "username": "user",
    "password": "pass",
    "port": 22
})

if ssh.connect():
    result = ssh.execute("ls -la")
    print(result)
    ssh.disconnect()
```

## Utility Functions

### Agent Communication

```python
from agentbeats.utils.agents import create_a2a_client, send_message_to_agent, send_message_to_agents
```

- `create_a2a_client(target_url: str) -> A2AClient`
- `send_message_to_agent(target_url: str, message: str) -> str`
- `send_message_to_agents(target_urls: List[str], message: str) -> Dict[str, str]`

### Environment Management

```python
from agentbeats.utils.environment import setup_container, cleanup_container, check_container_health
```

- `setup_container(config: Dict[str, Any]) -> bool`
- `cleanup_container(env_id: str) -> bool`
- `check_container_health(container_name: str) -> bool`

### SSH Tools

```python
from agentbeats.utils.commands import create_ssh_connect_tool
```

- `create_ssh_connect_tool(agent_instance, **defaults) -> function`

## Logging Functions

```python
from agentbeats.logging import (
    set_battle_context, log_ready, log_error, log_startup, log_shutdown,
    record_battle_event, record_battle_result, record_agent_action
)
```

### Context Management

- `set_battle_context(battle_id: str, agent_name: str, backend_url: str)`
- `get_battle_context() -> Dict[str, Any]`
- `clear_battle_context()`

### System Logging

- `log_ready()` - Log agent ready status
- `log_error(error: str)` - Log error messages
- `log_startup()` - Log startup events
- `log_shutdown()` - Log shutdown events

### Interaction History

- `record_battle_event(event_type: str, details: Dict[str, Any])`
- `record_battle_result(result: str, details: Dict[str, Any])`
- `record_agent_action(action: str, details: Dict[str, Any])`

## CLI Commands

### run_agent

Start an agent from a card file:

```bash
agentbeats run_agent agent_card.toml --tool tools.py --mcp http://localhost:8001
```

### run

Launch an agent with controller layer:

```bash
agentbeats run agent_card.toml --backend http://localhost:8000 --tool tools.py
```

## Configuration

### Agent Card Format (TOML)

```toml
name = "my_agent"
description = "A security contest agent"
host = "localhost"
port = 8001
skills = "Can perform SSH operations and communicate with other agents"
```

## Error Handling

All functions return appropriate error messages or raise exceptions when operations fail. Check return values and handle exceptions appropriately in your code. 