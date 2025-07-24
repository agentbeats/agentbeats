# Agent Communication

Utilities for A2A (Agent-to-Agent) communication in the AgentBeats SDK.

## Overview

The agent communication utilities provide functions for creating A2A clients and sending messages between agents using the A2A protocol.

## Functions

### create_a2a_client

Creates an A2A client for communicating with an agent at the specified target URL.

```python
from agentbeats.utils.agents import create_a2a_client

client = await create_a2a_client(target_url: str) -> A2AClient
```

#### Parameters

- `target_url` (str) - The URL of the target agent (e.g., "http://localhost:8001")

#### Returns

- `A2AClient` - An A2A client instance for communicating with the target agent

#### Example

```python
import asyncio
from agentbeats.utils.agents import create_a2a_client

async def connect_to_agent():
    client = await create_a2a_client("http://localhost:8001")
    return client

# Usage
client = asyncio.run(connect_to_agent())
```

### send_message_to_agent

Sends a message to another A2A agent and gets back the plain-text response.

```python
from agentbeats.utils.agents import send_message_to_agent

response = await send_message_to_agent(target_url: str, message: str) -> str
```

#### Parameters

- `target_url` (str) - The URL of the target agent
- `message` (str) - The message to send to the agent

#### Returns

- `str` - The plain-text response from the agent

#### Example

```python
import asyncio
from agentbeats.utils.agents import send_message_to_agent

async def communicate_with_agent():
    response = await send_message_to_agent(
        "http://localhost:8001",
        "Hello, can you help me with a task?"
    )
    print(f"Agent response: {response}")

# Usage
asyncio.run(communicate_with_agent())
```

### send_message_to_agents

Sends a message to multiple A2A agents concurrently and returns their responses.

```python
from agentbeats.utils.agents import send_message_to_agents

responses = await send_message_to_agents(target_urls: List[str], message: str) -> Dict[str, str]
```

#### Parameters

- `target_urls` (List[str]) - List of target agent URLs
- `message` (str) - The message to send to all agents

#### Returns

- `Dict[str, str]` - Dictionary mapping agent URLs to their responses

#### Example

```python
import asyncio
from agentbeats.utils.agents import send_message_to_agents

async def broadcast_to_agents():
    urls = [
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003"
    ]
    
    responses = await send_message_to_agents(
        urls,
        "Please report your current status"
    )
    
    for url, response in responses.items():
        print(f"Agent {url}: {response}")

# Usage
asyncio.run(broadcast_to_agents())
```

## Error Handling

All functions handle common error scenarios:

- **Connection errors**: Network issues or agent not available
- **Timeout errors**: Agent takes too long to respond
- **Protocol errors**: Invalid A2A protocol responses

Functions return appropriate error messages when operations fail.

## Usage Patterns

### Basic Agent Communication

```python
import asyncio
from agentbeats.utils.agents import send_message_to_agent

async def basic_communication():
    try:
        response = await send_message_to_agent(
            "http://localhost:8001",
            "What is your current status?"
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Communication failed: {e}")

asyncio.run(basic_communication())
```

### Multi-Agent Coordination

```python
import asyncio
from agentbeats.utils.agents import send_message_to_agents

async def coordinate_agents():
    agent_urls = [
        "http://red-agent:8001",
        "http://blue-agent:8002",
        "http://green-agent:8003"
    ]
    
    # Send status request to all agents
    status_responses = await send_message_to_agents(
        agent_urls,
        "Report your current status and capabilities"
    )
    
    # Process responses
    for url, response in status_responses.items():
        agent_name = url.split("//")[1].split(":")[0]
        print(f"{agent_name}: {response}")

asyncio.run(coordinate_agents())
```

### Agent Discovery and Communication

```python
import asyncio
from agentbeats.utils.agents import create_a2a_client, send_message_to_agent

async def discover_and_communicate():
    # First, discover available agents
    known_agents = [
        "http://localhost:8001",
        "http://localhost:8002"
    ]
    
    # Test communication with each agent
    for agent_url in known_agents:
        try:
            response = await send_message_to_agent(
                agent_url,
                "Are you available for coordination?"
            )
            print(f"Agent {agent_url} is available: {response}")
        except Exception as e:
            print(f"Agent {agent_url} is not available: {e}")

asyncio.run(discover_and_communicate())
```

## Integration with Agent Tools

You can integrate these functions into agent tools:

```python
from agentbeats import tool
from agentbeats.utils.agents import send_message_to_agent

@tool()
async def ask_other_agent(agent_url: str, question: str) -> str:
    """Ask a question to another agent."""
    try:
        response = await send_message_to_agent(agent_url, question)
        return f"Response from {agent_url}: {response}"
    except Exception as e:
        return f"Failed to communicate with {agent_url}: {e}"
```

## Best Practices

1. **Error Handling**: Always wrap communication calls in try-catch blocks
2. **Timeouts**: Be aware that agent communication may take time
3. **Concurrency**: Use `send_message_to_agents` for efficient multi-agent communication
4. **URL Management**: Keep agent URLs in configuration files
5. **Response Processing**: Handle different response formats appropriately

## Related Documentation

- [Getting Started](../getting-started.md) - Basic setup and usage
- [API Reference](../api-reference.md) - Complete API documentation
- [SSH Commands](ssh.md) - SSH utilities for remote operations 