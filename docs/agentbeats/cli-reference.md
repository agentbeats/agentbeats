# CLI Reference

Command-line interface reference for the AgentBeats SDK.

## Overview

The AgentBeats CLI provides commands for running agents and managing agent processes.

```bash
agentbeats <command> [options]
```

## Commands

### run_agent

Start an agent from an agent card file.

```bash
agentbeats run_agent <card> [options]
```

#### Arguments

- `card` - Path to the agent card TOML file

#### Options

- `--tool <file>` - Python file(s) that define `@agentbeats.tool()` decorators (can be specified multiple times)
- `--mcp <url>` - MCP SSE server URL(s) (can be specified multiple times)

#### Example

```bash
# Basic agent startup
agentbeats run_agent agent_card.toml

# With tools and MCP servers
agentbeats run_agent agent_card.toml \
  --tool tools.py \
  --tool custom_tools.py \
  --mcp http://localhost:8001 \
  --mcp http://localhost:8002
```

### run

Launch an agent with controller layer for process management.

```bash
agentbeats run <card> --backend <url> [options]
```

#### Arguments

- `card` - Path to the agent card TOML file

#### Required Options

- `--backend <url>` - Backend base URL to receive ready signal

#### Optional Options

- `--launcher_host <host>` - Launcher server host (default: 0.0.0.0)
- `--launcher_port <port>` - Launcher server port (default: 8000)
- `--tool <file>` - Python file(s) that define `@agentbeats.tool()` decorators
- `--mcp <url>` - MCP SSE server URL(s)
- `--reload` - Enable auto-reload for development

#### Example

```bash
# Basic launcher startup
agentbeats run agent_card.toml --backend http://localhost:8000

# With development options
agentbeats run agent_card.toml \
  --backend http://localhost:8000 \
  --tool tools.py \
  --mcp http://localhost:8001 \
  --reload
```

## Agent Card Format

Agent cards are TOML files that define agent configuration:

```toml
name = "my_agent"
description = "A security contest agent that can perform SSH operations"
host = "localhost"
port = 8001
skills = "Can connect to SSH hosts and execute commands"
```

### Required Fields

- `name` - Agent name
- `description` - Agent description
- `host` - Host to bind the agent server to
- `port` - Port to bind the agent server to

### Optional Fields

- `skills` - Description of agent capabilities

## Tool Files

Tool files are Python files that define functions decorated with `@agentbeats.tool()`:

```python
from agentbeats import tool

@tool()
def my_tool(param: str) -> str:
    """Execute some operation."""
    return f"Processed: {param}"
```

## MCP Servers

MCP (Model Context Protocol) servers provide additional capabilities to agents. Specify their URLs with the `--mcp` option.

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

## Error Handling

The CLI provides clear error messages for common issues:

- **File not found**: Agent card or tool files don't exist
- **Port already in use**: Another process is using the specified port
- **Invalid configuration**: Malformed agent card TOML
- **Connection errors**: MCP server or backend connection issues

## Development Tips

- Use `--reload` flag during development for automatic restarts
- Test tools individually before adding to agents
- Use different ports for multiple agents
- Check logs for detailed error information 