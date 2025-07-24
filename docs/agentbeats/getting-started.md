# Getting Started with AgentBeats SDK

Welcome to the AgentBeats SDK! This guide will help you get up and running quickly with the SDK for building and managing AI agents.

## Prerequisites

Before you begin, make sure you have:

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation

### Option 1: Install from Source

1. Clone the repository:
```bash
git clone <repository-url>
cd agentbeats_sdk
```

2. Create a virtual environment:
```bash
python -m venv temp_venv
source temp_venv/bin/activate  # On Windows: temp_venv\Scripts\activate
```

3. Install the SDK in development mode:
```bash
pip install -e .
```

### Option 2: Install with Demo Extras

To install with demo examples included:

```bash
pip install -e ".[demos]"
```

## Quick Start

### 1. Basic Agent Creation

Create a simple agent using the SDK:

```python
from agentbeats import AgentExecutor

# Create an agent executor
executor = AgentExecutor()

# Define your agent configuration
agent_config = {
    "name": "my_agent",
    "description": "A simple test agent",
    "model": "gpt-4",
    "system_prompt": "You are a helpful assistant."
}

# Create and run the agent
agent = executor.create_agent(agent_config)
response = agent.run("Hello, how are you?")
print(response)
```

### 2. Using Utility Functions

The SDK provides various utility functions for common tasks:

```python
from agentbeats.utils.agents import create_a2a_client, send_message_to_agent
from agentbeats.utils.environment import setup_container, check_container_health
from agentbeats.utils.commands import execute_ssh_command

# Agent-to-agent communication
client = create_a2a_client("agent1", "agent2")
response = send_message_to_agent(client, "Hello from agent1!")

# Container management
container_id = setup_container("my-container", "ubuntu:latest")
health = check_container_health(container_id)

# SSH operations
result = execute_ssh_command("user@host", "ls -la", password="password")
```

### 3. Running Demos

If you installed with demo extras, you can explore the included examples:

```bash
# List available demos
python -m agentbeats.demos

# Run a specific demo
python -m agentbeats.demos.sdk_demos
```

## Configuration

### Environment Variables

Set up your environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export AGENTBEATS_LOG_LEVEL="INFO"
```

### Logging Configuration

The SDK includes comprehensive logging capabilities:

```python
from agentbeats.utils.logging import setup_logging

# Setup logging with custom configuration
setup_logging(
    log_level="INFO",
    log_file="agentbeats.log",
    enable_console=True
)
```

## Project Structure

```
agentbeats_sdk/
├── src/agentbeats/
│   ├── __init__.py
│   ├── agent_executor.py      # Main agent execution logic
│   ├── agent_launcher.py      # Agent launching utilities
│   ├── cli.py                 # Command-line interface
│   ├── utils/
│   │   ├── agents/            # Agent communication utilities
│   │   ├── environment/       # Container and environment management
│   │   ├── commands/          # SSH and command execution
│   │   └── logging/           # Logging and interaction history
│   └── demos/                 # Example implementations
├── docs/                      # Documentation
└── pyproject.toml            # Project configuration
```

## CLI Usage

The SDK provides a command-line interface for common operations:

```bash
# Show help
python -m agentbeats --help

# Run an agent from configuration
python -m agentbeats run --config agent_config.yaml

# Launch multiple agents
python -m agentbeats launch --agents agent1.yaml agent2.yaml
```

## Next Steps

1. **Explore the Demos**: Check out the demo implementations in `src/agentbeats/demos/`
2. **Read the API Reference**: See `docs/api-reference.md` for detailed API documentation
3. **Check Utils Documentation**: Learn about utility functions in `docs/utils/`
4. **Review CLI Reference**: See `docs/cli-reference.md` for command-line options

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the correct virtual environment
2. **API Key Issues**: Verify your OpenAI API key is set correctly
3. **Container Issues**: Ensure Docker is running for container operations
4. **SSH Connection Issues**: Check network connectivity and credentials

### Getting Help

- Check the documentation in the `docs/` folder
- Review the demo implementations
- Check the logs for detailed error messages

## Examples

### Multi-Agent Communication

```python
from agentbeats.utils.agents import create_a2a_client, send_message_to_agents

# Create multiple agents
agents = ["agent1", "agent2", "agent3"]

# Send message to all agents
responses = send_message_to_agents(agents, "Hello everyone!")
```

### Container Workflow

```python
from agentbeats.utils.environment import setup_container, cleanup_container

# Setup and use a container
container_id = setup_container("test-container", "python:3.9")
try:
    # Your container operations here
    pass
finally:
    # Clean up
    cleanup_container(container_id)
```

This getting started guide should help you begin using the AgentBeats SDK effectively. For more detailed information, refer to the other documentation files in the `docs/` directory.
