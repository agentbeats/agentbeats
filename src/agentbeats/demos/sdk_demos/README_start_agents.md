# Agent Launcher Template

This is a simple agent launcher script template that can be easily adapted for different scenarios.

## Usage

### Current scenario (tensortrust)

```bash
# View all agent commands
python start_agents.py --show

# Start all agents in separate terminal windows
python start_agents.py

# Start all agents in current terminal
python start_agents.py --current

# Start specific agents (using indices)
python start_agents.py --agents 0 1    # Start Blue and Red agents

# Start specific agents (using names)
python start_agents.py --agents "Blue Agent" "Red Agent"
```

## Customization for New Scenarios

1. **Copy script**: Copy `start_agents.py` to your new scenario directory
2. **Modify configuration**: Only need to modify the configuration section at the top of the script:

```python
# Modify scenario name
SCENARIO_NAME = "your_scenario_name"

# Modify agent command list
AGENT_COMMANDS = [
    {
        "name": "Your Agent 1",
        "command": "agentbeats run agent1/config.toml --launcher_host 0.0.0.0 --launcher_port 9040 --backend http://localhost:9000"
    },
    {
        "name": "Your Agent 2", 
        "command": "agentbeats run agent2/config.toml --launcher_host 0.0.0.0 --launcher_port 9050 --backend http://localhost:9000"
    }
    # Add more agents...
]
```

3. **Save and use**: Save the file and use the same command line arguments

## Configuration Details

- **name**: Agent display name, shown in terminal title and logs
- **command**: Complete agentbeats launch command
