# TensorTrust Demos

Security contest agent examples demonstrating advanced capabilities for TensorTrust scenarios.

## Overview

The TensorTrust demos showcase agents designed for security contests and scenarios. These demos demonstrate advanced features including SSH operations, environment management, and agent coordination.

## Demo Categories

### TensorTrust from Scratch

Complete agent implementations built from the ground up for security contests.

```
demos/tensortrust_from_scratch/
├── red_agent/           # Red team agent
├── blue_agent/          # Blue team agent  
├── green_agent/         # Green team agent
├── start_agents.py      # Multi-agent startup script
└── README.md           # Detailed instructions
```

### TensorTrust with Utils

Enhanced agents that leverage the AgentBeats SDK utilities for improved functionality.

```
demos/tensortrust_with_utils/
├── red_agent/           # Red team agent with utilities
├── blue_agent/          # Blue team agent with utilities
├── green_agent/         # Green team agent with utilities
├── start_agents.py      # Multi-agent startup script
└── README.md           # Detailed instructions
```

## Agent Types

### Red Team Agent

Offensive security agent designed for penetration testing and vulnerability assessment.

**Key Capabilities:**
- SSH reconnaissance and exploitation
- Network scanning and enumeration
- Vulnerability assessment
- Privilege escalation attempts
- Data exfiltration simulation

**Example Tools:**
```python
@tool()
def scan_network(target: str) -> str:
    """Scan a target network for open ports and services."""
    # Implementation for network scanning
    pass

@tool()
def attempt_ssh_login(host: str, username: str, password: str) -> str:
    """Attempt SSH login with provided credentials."""
    # Implementation for SSH brute force
    pass
```

### Blue Team Agent

Defensive security agent focused on monitoring, detection, and response.

**Key Capabilities:**
- System monitoring and logging
- Intrusion detection
- Incident response
- Security event correlation
- Threat hunting

**Example Tools:**
```python
@tool()
def monitor_system_logs() -> str:
    """Monitor system logs for suspicious activity."""
    # Implementation for log monitoring
    pass

@tool()
def check_process_list() -> str:
    """Check running processes for suspicious activity."""
    # Implementation for process monitoring
    pass
```

### Green Team Agent

Neutral agent for environment management and coordination.

**Key Capabilities:**
- Environment setup and teardown
- Agent coordination
- Resource management
- Battle context tracking
- Infrastructure monitoring

**Example Tools:**
```python
@tool()
def setup_battle_environment() -> str:
    """Setup the battle environment with Docker containers."""
    # Implementation for environment setup
    pass

@tool()
def coordinate_agents() -> str:
    """Coordinate communication between red and blue agents."""
    # Implementation for agent coordination
    pass
```

## Running the Demos

### Starting All Agents

Use the provided startup script to launch all agents:

```bash
# Navigate to the demo directory
cd demos/tensortrust_from_scratch/

# Start all agents
python start_agents.py
```

### Individual Agent Startup

Start agents individually for testing:

```bash
# Red team agent
agentbeats run_agent red_agent/agent_card.toml --tool red_agent/tools.py

# Blue team agent  
agentbeats run_agent blue_agent/agent_card.toml --tool blue_agent/tools.py

# Green team agent
agentbeats run_agent green_agent/agent_card.toml --tool green_agent/tools.py
```

### With Launcher (Production)

Use the launcher for production scenarios:

```bash
# Red team with launcher
agentbeats run red_agent/agent_card.toml \
  --backend http://localhost:8000 \
  --tool red_agent/tools.py

# Blue team with launcher
agentbeats run blue_agent/agent_card.toml \
  --backend http://localhost:8000 \
  --tool blue_agent/tools.py
```

## Agent Cards

### Red Team Agent Card

```toml
name = "red_team_agent"
description = "Offensive security agent for penetration testing"
host = "localhost"
port = 8001
skills = "Network scanning, SSH exploitation, vulnerability assessment"
```

### Blue Team Agent Card

```toml
name = "blue_team_agent"
description = "Defensive security agent for monitoring and response"
host = "localhost"
port = 8002
skills = "System monitoring, intrusion detection, incident response"
```

### Green Team Agent Card

```toml
name = "green_team_agent"
description = "Neutral agent for environment management"
host = "localhost"
port = 8003
skills = "Environment setup, agent coordination, resource management"
```

## Advanced Features

### SSH Integration

Agents use the SSHClient for remote operations:

```python
from agentbeats.utils.commands import SSHClient

@tool()
def remote_system_check(host: str, username: str, password: str) -> str:
    """Check system information on a remote host."""
    ssh = SSHClient(host, {"username": username, "password": password})
    
    if ssh.connect():
        result = ssh.execute("uname -a")
        ssh.disconnect()
        return result
    return "Failed to connect"
```

### Environment Management

Agents can manage Docker environments:

```python
from agentbeats.utils.environment import setup_container, cleanup_container

@tool()
async def setup_battle_env() -> str:
    """Setup the battle environment."""
    config = {"docker_dir": "docker"}
    success = await setup_container(config)
    return "Environment ready" if success else "Setup failed"
```

### Agent Communication

Agents can communicate with each other:

```python
from agentbeats.utils.agents import send_message_to_agent

@tool()
async def ask_blue_team(question: str) -> str:
    """Ask a question to the blue team agent."""
    response = await send_message_to_agent(
        "http://localhost:8002",
        question
    )
    return response
```

## Battle Scenarios

### Scenario 1: Network Reconnaissance

1. **Red Team**: Scans network for vulnerabilities
2. **Blue Team**: Monitors for scanning activity
3. **Green Team**: Coordinates and tracks progress

### Scenario 2: SSH Exploitation

1. **Red Team**: Attempts SSH brute force attacks
2. **Blue Team**: Detects failed login attempts
3. **Green Team**: Manages environment state

### Scenario 3: Privilege Escalation

1. **Red Team**: Attempts privilege escalation
2. **Blue Team**: Monitors for suspicious processes
3. **Green Team**: Tracks battle context and events

## Customization

### Adding New Tools

Extend agent capabilities by adding custom tools:

```python
# red_agent/custom_tools.py
from agentbeats import tool

@tool()
def custom_exploit(target: str) -> str:
    """Custom exploitation tool."""
    # Implementation
    return f"Exploited {target}"
```

### Modifying Agent Behavior

Update agent cards to change behavior:

```toml
name = "custom_red_agent"
description = "Custom red team agent with specialized tools"
host = "0.0.0.0"
port = 8004
skills = "Custom exploitation techniques, advanced reconnaissance"
```

### Environment Configuration

Configure Docker environments for different scenarios:

```yaml
# docker/custom-scenario.yml
version: '3.8'
services:
  vulnerable-web:
    image: vulnerable-web-app
    ports:
      - "8080:80"
  
  target-database:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: weak_password
```

## Best Practices

1. **Agent Isolation**: Use separate ports and networks for different agents
2. **Logging**: Implement comprehensive logging for all operations
3. **Error Handling**: Robust error handling for network and system operations
4. **Resource Management**: Clean up resources after operations
5. **Security**: Use secure credentials and avoid hardcoding sensitive data

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure agents use different ports
2. **SSH Connection Issues**: Check SSH service and credentials
3. **Docker Problems**: Verify Docker is running and accessible
4. **Agent Communication**: Check network connectivity between agents

### Debug Commands

```bash
# Check agent status
curl http://localhost:8001/.well-known/agent.json

# View agent logs
docker logs agent_container

# Test SSH connectivity
ssh username@target_host
```

## Related Documentation

- [Getting Started](../getting-started.md) - Basic setup and usage
- [SSH Commands](../utils/ssh.md) - SSH utilities for remote operations
- [Environment Management](../utils/environment.md) - Docker environment utilities
- [Agent Communication](../utils/agents.md) - Agent-to-agent communication
- [API Reference](../api-reference.md) - Complete API documentation 