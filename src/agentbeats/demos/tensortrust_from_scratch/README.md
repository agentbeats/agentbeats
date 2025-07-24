# README

## How-to run?

Run a game:

```
# Suppose you host your frontend / backend previously...

cd scenarios/tensortrust_mock
# Blue Agent
agentbeats run blue_agent/blue_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9010 --backend http://localhost:9000
# Red Agent
agentbeats run red_agent/red_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9020 --backend http://localhost:9000
# Green Agent
agentbeats run green_agent/green_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9030 --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool green_agent/tools.py

# Then register agent & host battle in frontend plz.
```

## Bonus: Agent-only mode

If you prefer agent-only mode (without wrapper server):
```
cd scenarios/tensortrust_mock
agentbeats run_agent agents/blue_agent/blue_agent_card.toml
agentbeats run_agent agents/red_agent/red_agent_card.toml
agentbeats run_agent agents/green_agent/green_agent_card.toml --mcp ['http://localhost:9001/'] --tool 'agents/green_agent/tools.py'
```
