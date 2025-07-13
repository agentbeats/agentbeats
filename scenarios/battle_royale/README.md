# Battle Royale Scenario

A competitive AI agent scenario where multiple red agents compete by creating web services in a Docker container environment, while a green agent monitors and judges the competition.

## 🎯 Overview

In this battle royale scenario:
- **Red Agents**: Compete by creating web services on port 80 in a shared Docker container
- **Green Agent**: Monitors all services, calculates scores based on uptime, and determines the winner
- **Docker Arena**: Provides the isolated environment where agents compete
- **Scoring**: Based on service uptime percentage and performance metrics

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Red Agent 1   │    │   Red Agent 2   │    │   Red Agent 3   │
│   (Port 8001)   │    │   (Port 8002)   │    │   (Port 8003)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Green Agent    │
                    │  (Port 8011)    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Docker Arena   │
                    │  (Port 9001)    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Battle Arena   │
                    │  Container      │
                    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- Docker and Docker Compose
- SSH client
- OpenAI API key (for OpenRouter)

### Environment Variables

Set these environment variables for OpenRouter access:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_API_BASE="https://openrouter.ai/api/v1"
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install battle royale specific dependencies
pip install -r requirements.txt

# Or install from root directory
pip install -r ../../requirements.txt
```

### 2. Start the Docker Arena

```bash
cd docker
docker-compose up -d
```

This starts:
- Battle arena container with SSH access
- Service manager API on port 9001
- Monitoring dashboard on port 9002

### 3. Start the Agents

```bash
# Start green agent (monitor/judge)
cd agents
python agent_launcher.py green_agent

# In separate terminals, start red agents
python agent_launcher.py red_agent --port 8001
python agent_launcher.py red_agent --port 8002
python agent_launcher.py red_agent --port 8003
```

### 4. Run the Battle

```bash
# Run the complete battle simulation
python battle_orchestrator.py
```

Or manually orchestrate:

```bash
# Create battle arena
curl -X POST http://localhost:8011/a2a \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Create a new battle arena"}]}'

# Start battle
curl -X POST http://localhost:8011/a2a \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Start the battle royale"}]}'
```

## 🧪 Testing

### Run Comprehensive Tests

```bash
cd tests
python test_battle_royale_comprehensive.py
```

### Individual Component Tests

```bash
# Test agent basics
python test_agent_basics.py

# Test green agent tools
python test_green_agent_tools.py

# Test red agent tools
python test_red_agent_tools.py

# Test Docker environment
python test_docker_environment.py
```

### Manual Testing

```bash
# Test agent health
curl http://localhost:8011/.well-known/agent.json

# Test A2A communication
curl -X POST http://localhost:8011/a2a \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

# Test Docker arena
curl http://localhost:9001/health
```

## 📊 Monitoring

### Web Dashboard

Access the monitoring dashboard at: http://localhost:9002

Features:
- Real-time agent status
- Service uptime monitoring
- Battle progress tracking
- Live logs
- Performance metrics

### API Endpoints

- **Health Check**: `GET /health`
- **Agent Status**: `GET /api/agents`
- **Service Status**: `GET /api/services`
- **Battle Info**: `GET /api/battle`
- **Logs**: `GET /api/logs`

## 🤖 Agent Details

### Green Agent (Monitor/Judge)

**Port**: 8011
**Role**: Battle monitor and judge
**Capabilities**:
- Docker container management
- Service monitoring and scoring
- Battle orchestration
- Winner determination
- Communication with red agents

**MCP Tools**:
- `create_battle_arena`: Initialize battle environment
- `monitor_services`: Check service status and uptime
- `calculate_scores`: Compute agent scores
- `determine_winner`: Select battle winner
- `communicate_with_agents`: Send messages to red agents

### Red Agents (Competitors)

**Ports**: 8001, 8002, 8003
**Role**: Web service competitors
**Capabilities**:
- SSH connection to battle arena
- Web service creation and management
- Service blocking and sabotage
- Status monitoring
- Service reset and recovery

**MCP Tools**:
- `ssh_connect`: Connect to battle arena
- `execute_ssh_command`: Run commands via SSH
- `create_web_service`: Start web service on port 80
- `block_service`: Block other agents' services
- `check_service_status`: Monitor service health
- `reset_service`: Restart failed services

## 🏆 Battle Flow

1. **Setup Phase**
   - Green agent creates battle arena
   - Red agents connect via SSH
   - Initial service deployment

2. **Competition Phase**
   - Red agents create web services
   - Agents attempt to block each other
   - Green agent monitors uptime
   - Continuous scoring calculation

3. **Judgment Phase**
   - Green agent calculates final scores
   - Winner determination based on uptime
   - Battle summary generation

## 📁 File Structure

```
battle_royale/
├── agents/
│   ├── green_agent/
│   │   ├── main.py
│   │   ├── agent_executor.py
│   │   └── agent_card.toml
│   ├── red_agent/
│   │   ├── main.py
│   │   ├── agent_executor.py
│   │   └── agent_card.toml
│   └── agent_launcher.py
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── service_manager.py
│   └── monitor-html/
│       └── dashboard.html
├── tests/
│   ├── test_battle_royale_comprehensive.py
│   ├── test_agent_basics.py
│   ├── test_green_agent_tools.py
│   ├── test_red_agent_tools.py
│   └── test_docker_environment.py
├── battle_orchestrator.py
├── requirements.txt
└── README.md
```

## 🔧 Configuration

### Agent Configuration

Edit `agents/*/agent_card.toml` to modify:
- Agent name and description
- Model configuration
- Tool definitions
- Communication settings

### Docker Configuration

Edit `docker/docker-compose.yml` to modify:
- Container resources
- Port mappings
- Environment variables
- Volume mounts

### Battle Configuration

Edit `battle_orchestrator.py` to modify:
- Battle duration
- Monitoring intervals
- Agent URLs
- Scoring parameters

## 🐛 Troubleshooting

### Common Issues

**Agents not starting**:
```bash
# Check if ports are available
lsof -i :8001,8002,8003,8011

# Kill processes on ports
pkill -f "python.*agent_launcher"
```

**Docker arena not accessible**:
```bash
# Check Docker services
docker-compose ps

# Restart Docker arena
docker-compose down && docker-compose up -d
```

**SSH connection issues**:
```bash
# Test SSH manually
ssh -p 2222 root@localhost

# Check SSH keys
ls -la docker/ssh/
```

**API communication errors**:
```bash
# Check agent health
curl http://localhost:8011/.well-known/agent.json

# Check logs
tail -f battle_royale.log
```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python battle_orchestrator.py
```

### Reset Environment

```bash
# Stop all services
docker-compose down
pkill -f "python.*agent_launcher"

# Clean up
docker system prune -f
rm -f battle_royale.log battle_summary.json
```

## 📈 Performance Tuning

### Agent Performance

- **Model Selection**: Use faster models for real-time responses
- **Tool Optimization**: Minimize tool call overhead
- **Connection Pooling**: Reuse SSH connections

### Docker Optimization

- **Resource Limits**: Set appropriate CPU/memory limits
- **Network Optimization**: Use host networking for better performance
- **Volume Caching**: Cache frequently accessed data

### Monitoring Optimization

- **Polling Frequency**: Adjust monitoring intervals
- **Data Retention**: Limit log and metric storage
- **Dashboard Updates**: Optimize real-time updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is part of the AgentBeats framework. See the main project license for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test results
3. Check the logs in `battle_royale.log`
4. Open an issue with detailed error information 