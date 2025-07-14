# Battle Royale Docker Environment

This Docker environment provides a controlled arena for AI agents to compete in a battle royale scenario.

## Quick Start

1. **Build and start the environment:**
   ```bash
   cd scenarios/battle_royale/docker
   docker-compose up -d
   ```

2. **Test SSH access:**
   ```bash
   ssh battle@localhost -p 2222
   # Password: battle123
   ```

3. **Check health:**
   ```bash
   curl http://localhost:8080/health
   ```

## Environment Details

### Ports
- **SSH**: `localhost:2222` (user: `battle`, password: `battle123`)
- **Health Check**: `http://localhost:8080/health`
- **Service Manager**: `http://localhost:9000`
- **Web Services**: `http://localhost:8081`

### Directory Structure
```
/battle/
├── arena/           # Battle arena files
├── logs/            # System and service logs
├── services/        # Agent web services
└── status.json      # Current battle status
```

### Available Tools
- **Python 3** with Flask, FastAPI, requests
- **Web servers**: nginx, apache2
- **Network tools**: curl, wget, netcat, telnet
- **System tools**: htop, vim, nano
- **Monitoring**: psutil, system monitoring

## Service Manager API

The service manager runs on port 9000 and provides these endpoints:

### GET /services
List all registered services
```bash
curl http://localhost:9000/services
```

### POST /register
Register a new service
```bash
curl -X POST http://localhost:9000/register \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "red_1", "service_type": "web", "port": 80}'
```

### POST /start
Start a service
```bash
curl -X POST http://localhost:9000/start \
  -H "Content-Type: application/json" \
  -d '{"service_id": "red_1_1234567890", "command": "python3 -m http.server 80"}'
```

### POST /stop
Stop a service
```bash
curl -X POST http://localhost:9000/stop \
  -H "Content-Type: application/json" \
  -d '{"service_id": "red_1_1234567890"}'
```

### POST /check
Check service health
```bash
curl -X POST http://localhost:9000/check \
  -H "Content-Type: application/json" \
  -d '{"service_id": "red_1_1234567890"}'
```

## Battle Rules

1. **Objective**: Create a web service on port 80 that serves your agent name
2. **Tools**: Use SSH to access the environment and deploy your service
3. **Competition**: Agents can attempt to block each other's services
4. **Scoring**: Based on service uptime percentage
5. **Winner**: Agent with the highest uptime score

## Testing the Environment

### SSH Test
```bash
ssh battle@localhost -p 2222
# Once connected:
whoami
pwd
ls -la /battle
```

### Web Service Test
```bash
# From inside the container:
python3 -c "
import http.server
import socketserver
PORT = 80
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer((\"\", PORT), Handler) as httpd:
    print(f'Server running on port {PORT}')
    httpd.serve_forever()
"
```

### Service Manager Test
```bash
# Register a service
curl -X POST http://localhost:9000/register \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "test", "service_type": "web"}'

# List services
curl http://localhost:9000/services
```

## Troubleshooting

### Container won't start
```bash
docker-compose logs battle-arena
```

### SSH connection refused
```bash
docker-compose restart battle-arena
```

### Port conflicts
Check if ports 2222, 8080, 9000, or 8081 are already in use:
```bash
lsof -i :2222
lsof -i :8080
lsof -i :9000
lsof -i :8081
```

## Cleanup

```bash
docker-compose down
docker-compose down -v  # Remove volumes too
``` 