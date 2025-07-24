# SSH Commands

Utilities for SSH connection and command execution in the AgentBeats SDK.

## Overview

The SSH utilities provide a clean, class-based interface for establishing SSH connections and executing commands on remote hosts. This is particularly useful for agents that need to perform remote operations during security contests.

## SSHClient Class

The main SSH client class for remote command execution.

```python
from agentbeats.utils.commands import SSHClient

ssh = SSHClient(host: str, credentials: Dict[str, Any])
```

### Constructor

```python
SSHClient(host: str, credentials: Dict[str, Any])
```

#### Parameters

- `host` (str) - The target hostname or IP address
- `credentials` (Dict[str, Any]) - SSH credentials containing:
  - `username` (str, optional) - SSH username (default: "root")
  - `password` (str, optional) - SSH password (default: "")
  - `port` (int, optional) - SSH port (default: 22)

### Methods

#### connect()

Establishes an SSH connection to the target host.

```python
success = ssh.connect() -> bool
```

**Returns**: `bool` - True if connection successful, False otherwise

#### execute(command: str)

Executes a command on the remote host.

```python
result = ssh.execute(command: str) -> str
```

**Parameters**:
- `command` (str) - The command to execute

**Returns**: `str` - Command output with status information

#### disconnect()

Closes the SSH connection.

```python
ssh.disconnect()
```

## Usage Examples

### Basic SSH Operations

```python
from agentbeats.utils.commands import SSHClient

# Create SSH client
ssh = SSHClient("host.com", {
    "username": "user",
    "password": "password",
    "port": 22
})

# Connect and execute commands
if ssh.connect():
    # Execute a simple command
    result = ssh.execute("ls -la")
    print(result)
    
    # Execute another command
    result = ssh.execute("pwd")
    print(result)
    
    # Clean up
    ssh.disconnect()
else:
    print("Failed to connect to SSH host")
```

### Multiple Commands

```python
from agentbeats.utils.commands import SSHClient

def perform_remote_operations(host: str, credentials: dict):
    ssh = SSHClient(host, credentials)
    
    if not ssh.connect():
        return "Failed to connect"
    
    commands = [
        "whoami",
        "pwd",
        "ls -la",
        "ps aux | head -10"
    ]
    
    results = []
    for cmd in commands:
        result = ssh.execute(cmd)
        results.append(f"Command: {cmd}\n{result}\n")
    
    ssh.disconnect()
    return "\n".join(results)

# Usage
credentials = {"username": "user", "password": "pass"}
results = perform_remote_operations("host.com", credentials)
print(results)
```

### Error Handling

```python
from agentbeats.utils.commands import SSHClient

def safe_ssh_operation(host: str, credentials: dict, command: str):
    ssh = SSHClient(host, credentials)
    
    try:
        if not ssh.connect():
            return f"Failed to connect to {host}"
        
        result = ssh.execute(command)
        return result
        
    except Exception as e:
        return f"SSH operation failed: {str(e)}"
    finally:
        ssh.disconnect()

# Usage
result = safe_ssh_operation(
    "host.com",
    {"username": "user", "password": "pass"},
    "cat /etc/passwd"
)
print(result)
```

## Agent Integration

### Using SSHClient in Agent Tools

```python
from agentbeats import tool
from agentbeats.utils.commands import SSHClient

@tool()
def execute_remote_command(host: str, username: str, password: str, command: str) -> str:
    """Execute a command on a remote host via SSH."""
    credentials = {
        "username": username,
        "password": password,
        "port": 22
    }
    
    ssh = SSHClient(host, credentials)
    
    if not ssh.connect():
        return f"Failed to connect to {host}"
    
    try:
        result = ssh.execute(command)
        return result
    finally:
        ssh.disconnect()

@tool()
def check_remote_system(host: str, username: str, password: str) -> str:
    """Check system information on a remote host."""
    credentials = {"username": username, "password": password}
    ssh = SSHClient(host, credentials)
    
    if not ssh.connect():
        return f"Failed to connect to {host}"
    
    try:
        # Get system info
        os_info = ssh.execute("uname -a")
        disk_usage = ssh.execute("df -h")
        memory_info = ssh.execute("free -h")
        
        return f"System Information:\n{os_info}\n\nDisk Usage:\n{disk_usage}\n\nMemory:\n{memory_info}"
    finally:
        ssh.disconnect()
```

### SSH Tool Creation

```python
from agentbeats.utils.commands import create_ssh_connect_tool

# Create SSH tool for agent integration
ssh_tool = create_ssh_connect_tool(
    agent_instance,
    default_host="localhost",
    default_port=22,
    default_username="root",
    default_password=""
)

# The agent can now use the SSH tool
# agent_instance.ssh_client will be available after connection
```

## Command Output Format

The `execute()` method returns formatted output including:

- Command executed
- Exit status
- Standard output
- Standard error (if any)

Example output:
```
Success: Command: ls -la
Exit Status: 0
Output:
total 8
drwxr-xr-x  2 user user 4096 Jan 1 12:00 .
drwxr-xr-x 10 user user 4096 Jan 1 12:00 ..
-rw-r--r--  1 user user    0 Jan 1 12:00 file.txt
```

## Best Practices

1. **Connection Management**: Always call `disconnect()` when done
2. **Error Handling**: Wrap SSH operations in try-catch blocks
3. **Credentials**: Store credentials securely, not in code
4. **Command Validation**: Validate commands before execution
5. **Resource Cleanup**: Use context managers or finally blocks

### Secure Credential Handling

```python
import os
from agentbeats.utils.commands import SSHClient

def get_ssh_client(host: str):
    # Get credentials from environment variables
    username = os.getenv("SSH_USERNAME", "root")
    password = os.getenv("SSH_PASSWORD", "")
    port = int(os.getenv("SSH_PORT", "22"))
    
    credentials = {
        "username": username,
        "password": password,
        "port": port
    }
    
    return SSHClient(host, credentials)

# Usage
ssh = get_ssh_client("host.com")
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if SSH service is running on target host
2. **Authentication Failed**: Verify username and password
3. **Permission Denied**: Check user permissions on target host
4. **Timeout**: Check network connectivity and firewall settings

### Debug Commands

```bash
# Test SSH connection manually
ssh username@host.com

# Check SSH service status
sudo systemctl status ssh

# View SSH logs
sudo journalctl -u ssh
```

## Related Documentation

- [Getting Started](../getting-started.md) - Basic setup and usage
- [API Reference](../api-reference.md) - Complete API documentation
- [Agent Communication](agents.md) - Agent-to-agent communication utilities 