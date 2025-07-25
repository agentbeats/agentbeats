# Environment Management

Utilities for managing Docker containers and infrastructure in the AgentBeats SDK.

## Overview

The environment management utilities provide functions for setting up, managing, and cleaning up Docker container environments used in security contests and scenarios.

## Functions

### setup_container

Sets up a Docker container environment using docker-compose.

```python
from agentbeats.utils.environment import setup_container

success = await setup_container(config: Dict[str, Any]) -> bool
```

#### Parameters

- `config` (Dict[str, Any]) - Configuration dictionary containing:
  - `docker_dir` (str, optional) - Path to Docker directory (default: "docker")
  - `compose_file` (str, optional) - Docker Compose file name (default: "docker-compose.yml")

#### Returns

- `bool` - True if setup was successful, False otherwise

#### Example

```python
import asyncio
from agentbeats.utils.environment import setup_container

async def setup_environment():
    config = {
        "docker_dir": "docker",
        "compose_file": "docker-compose.yml"
    }
    
    success = await setup_container(config)
    if success:
        print("Docker environment started successfully")
    else:
        print("Failed to start Docker environment")

# Usage
asyncio.run(setup_environment())
```

### cleanup_container

Destroys and resets a container environment.

```python
from agentbeats.utils.environment import cleanup_container

success = await cleanup_container(env_id: str) -> bool
```

#### Parameters

- `env_id` (str) - Environment identifier for logging purposes

#### Returns

- `bool` - True if cleanup was successful, False otherwise

#### Example

```python
import asyncio
from agentbeats.utils.environment import cleanup_container

async def cleanup_environment():
    success = await cleanup_container("battle_env_001")
    if success:
        print("Environment cleaned up successfully")
    else:
        print("Failed to cleanup environment")

# Usage
asyncio.run(cleanup_environment())
```

### check_container_health

Checks the health status of a Docker container.

```python
from agentbeats.utils.environment import check_container_health

healthy = await check_container_health(container_name: str) -> bool
```

#### Parameters

- `container_name` (str) - Name of the container to check

#### Returns

- `bool` - True if container is healthy and running, False otherwise

#### Example

```python
import asyncio
from agentbeats.utils.environment import check_container_health

async def monitor_container():
    healthy = await check_container_health("web-server")
    if healthy:
        print("Container is healthy and running")
    else:
        print("Container is not healthy or not running")

# Usage
asyncio.run(monitor_container())
```

## Configuration

### Docker Compose Configuration

The utilities expect a standard Docker Compose setup:

```yaml
# docker-compose.yml
version: '3.8'
services:
  web-server:
    image: nginx:alpine
    ports:
      - "8080:80"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  database:
    image: postgres:13
    environment:
      POSTGRES_DB: agentbeats
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d agentbeats"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Configuration Dictionary

```python
config = {
    "docker_dir": "docker",           # Path to directory containing docker-compose.yml
    "compose_file": "docker-compose.yml"  # Name of the compose file
}
```

## Usage Patterns

### Complete Environment Lifecycle

```python
import asyncio
from agentbeats.utils.environment import setup_container, cleanup_container, check_container_health

async def manage_environment():
    # Setup environment
    config = {"docker_dir": "docker"}
    if await setup_container(config):
        print("Environment setup complete")
        
        # Check health
        if await check_container_health("web-server"):
            print("Web server is healthy")
        
        # ... perform operations ...
        
        # Cleanup
        await cleanup_container("battle_env")
    else:
        print("Failed to setup environment")

asyncio.run(manage_environment())
```

### Environment Monitoring

```python
import asyncio
import time
from agentbeats.utils.environment import check_container_health

async def monitor_containers():
    containers = ["web-server", "database", "redis"]
    
    while True:
        print(f"Health check at {time.strftime('%H:%M:%S')}")
        
        for container in containers:
            healthy = await check_container_health(container)
            status = "✅ Healthy" if healthy else "❌ Unhealthy"
            print(f"  {container}: {status}")
        
        await asyncio.sleep(60)  # Check every minute

# Usage
asyncio.run(monitor_containers())
```

### Error Handling

```python
import asyncio
from agentbeats.utils.environment import setup_container

async def robust_setup():
    try:
        config = {"docker_dir": "docker"}
        success = await setup_container(config)
        
        if success:
            print("Environment ready")
            return True
        else:
            print("Setup failed")
            return False
            
    except Exception as e:
        print(f"Setup error: {e}")
        return False

# Usage
success = asyncio.run(robust_setup())
```

## Integration with Agent Tools

You can integrate these functions into agent tools:

```python
from agentbeats import tool
from agentbeats.utils.environment import setup_container, cleanup_container

@tool()
async def setup_battle_environment(docker_dir: str = "docker") -> str:
    """Setup the battle environment."""
    config = {"docker_dir": docker_dir}
    success = await setup_container(config)
    
    if success:
        return "Battle environment setup complete"
    else:
        return "Failed to setup battle environment"

@tool()
async def cleanup_battle_environment(env_id: str) -> str:
    """Cleanup the battle environment."""
    success = await cleanup_container(env_id)
    
    if success:
        return f"Environment {env_id} cleaned up successfully"
    else:
        return f"Failed to cleanup environment {env_id}"
```

## Best Practices

1. **Health Checks**: Always include health checks in your Docker Compose files
2. **Error Handling**: Wrap environment operations in try-catch blocks
3. **Resource Management**: Clean up environments after use
4. **Monitoring**: Regularly check container health during long-running operations
5. **Configuration**: Use configuration files for environment settings

## Troubleshooting

### Common Issues

1. **Docker not running**: Ensure Docker daemon is started
2. **Port conflicts**: Check for port conflicts in docker-compose.yml
3. **Permission issues**: Ensure proper permissions for Docker operations
4. **Resource limits**: Monitor system resources during container operations

### Debug Commands

```bash
# Check Docker status
docker ps

# View container logs
docker-compose logs

# Check container health
docker inspect --format='{{.State.Health.Status}}' container_name
```

## Related Documentation

- [Getting Started](../getting-started.md) - Basic setup and usage
- [API Reference](../api-reference.md) - Complete API documentation
- [SSH Commands](ssh.md) - SSH utilities for remote operations 