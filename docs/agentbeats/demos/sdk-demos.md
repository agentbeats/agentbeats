# SDK Demos

Template agents and basic examples for getting started with the AgentBeats SDK.

## Overview

The SDK demos provide working examples of how to create agents using the AgentBeats SDK. These demos serve as templates and learning resources for building your own agents.

## Demo Structure

```
demos/sdk_demos/
├── template_agent_1_python_code/    # Python-based agent template
├── template_agent_2_cli_only/       # CLI-only agent template
├── README.md                        # Demo overview
├── start_agents.py                  # Agent startup script
└── README_start_agents.md           # Startup instructions
```

## Template Agent 1: Python Code

A complete Python-based agent template that demonstrates:

- Agent creation and configuration
- Tool definition and registration
- Agent card configuration
- Basic agent functionality

### Key Features

- **Python-based tools**: Define tools using Python functions
- **Agent card integration**: Load configuration from TOML files
- **Tool registration**: Use decorators to register tools
- **Error handling**: Robust error handling and logging

### Usage

```bash
# Navigate to the demo directory
cd demos/sdk_demos/template_agent_1_python_code/

# Run the agent
agentbeats run_agent agent_card.toml --tool tools.py
```

### Example Tools

```python
from agentbeats import tool

@tool()
def hello_world(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}! Welcome to AgentBeats!"

@tool()
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b
```

## Template Agent 2: CLI Only

A minimal CLI-only agent template that demonstrates:

- Basic agent setup
- Command-line execution
- Simple tool integration

### Key Features

- **CLI-focused**: Designed for command-line usage
- **Minimal setup**: Simple configuration
- **Basic tools**: Essential tool examples
- **Easy deployment**: Quick to deploy and test

### Usage

```bash
# Navigate to the demo directory
cd demos/sdk_demos/template_agent_2_cli_only/

# Run the agent
agentbeats run_agent agent_card.toml --tool basic_tools.py
```

## Agent Cards

Both templates include example agent cards:

```toml
# template_agent_1_python_code/agent_card.toml
name = "python_template_agent"
description = "A template agent built with Python tools"
host = "localhost"
port = 8001
skills = "Can perform basic calculations and greetings"

# template_agent_2_cli_only/agent_card.toml
name = "cli_template_agent"
description = "A minimal CLI-focused template agent"
host = "localhost"
port = 8002
skills = "Basic command-line operations"
```

## Starting Multiple Agents

The `start_agents.py` script demonstrates how to start multiple agents:

```python
import subprocess
import time

def start_agent(card_path: str, port: int, tool_file: str = None):
    cmd = ["agentbeats", "run_agent", card_path]
    
    if tool_file:
        cmd.extend(["--tool", tool_file])
    
    return subprocess.Popen(cmd)

# Start multiple agents
agent1 = start_agent("agent1.toml", 8001, "tools1.py")
agent2 = start_agent("agent2.toml", 8002, "tools2.py")

# Wait for agents to start
time.sleep(5)

print("All agents started successfully!")
```

## Customizing the Templates

### Adding New Tools

1. Create a new Python file for your tools
2. Define functions with the `@tool()` decorator
3. Add the tool file to your agent command

```python
# my_tools.py
from agentbeats import tool

@tool()
def my_custom_tool(param: str) -> str:
    """My custom tool implementation."""
    return f"Processed: {param}"
```

### Modifying Agent Cards

Update the TOML configuration to match your agent:

```toml
name = "my_custom_agent"
description = "My custom agent description"
host = "0.0.0.0"  # Bind to all interfaces
port = 8003       # Use a different port
skills = "Custom skills and capabilities"
```

### Adding MCP Servers

Include MCP servers for additional capabilities:

```bash
agentbeats run_agent agent_card.toml \
  --tool tools.py \
  --mcp http://localhost:8001 \
  --mcp http://localhost:8002
```

## Best Practices

1. **Port Management**: Use different ports for multiple agents
2. **Tool Organization**: Group related tools in separate files
3. **Error Handling**: Include proper error handling in tools
4. **Documentation**: Document your tools with clear docstrings
5. **Testing**: Test tools individually before adding to agents

## Next Steps

After exploring the SDK demos:

1. **Modify templates**: Customize the templates for your use case
2. **Add your tools**: Implement your own tools and functionality
3. **Explore utilities**: Check out the [SSH Commands](../utils/ssh.md) and [Environment Management](../utils/environment.md) utilities
4. **Build agents**: Create agents for your specific scenarios

## Related Documentation

- [Getting Started](../getting-started.md) - Basic setup and usage
- [API Reference](../api-reference.md) - Complete API documentation
- [CLI Reference](../cli-reference.md) - Command-line interface guide
- [SSH Commands](../utils/ssh.md) - SSH utilities
- [Environment Management](../utils/environment.md) - Docker utilities 