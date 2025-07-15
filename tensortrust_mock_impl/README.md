# README

## How-to run?

Install environment:

```
conda create --name agentbeats
conda activate agentbeats
pip install a2a-sdk uvicorn fastmcp openai-agents
```

Run a game:

```
# backend & mcp
python -m tensortrust_mock_impl.backend.run
python -m tensortrust_mock_impl.backend.mcp.logging_mcp

# setup agents
cd tensortrust_mock_impl
agentbeats run_agent agents/blue_agent/blue_agent_card.toml
agentbeats run_agent agents/red_agent/red_agent_card.toml
agentbeats run_agent agents/green_agent/green_agent_card.toml --mcp ['http://nuggets.puppy9.com:9001/'] --tool 'agents/green_agent/tools.py'

# start game
python tensortrust_test.py
```

Run template agent:
```
cd tensortrust_mock_impl/agents/template_agent_2_cli_only
# Run full launcher + agent
agentbeats run agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9010 --backend http://nuggets.puppy9.com:9000 --mcp http://localhost:9123/sse --tool tools.py
# If you prefer run agent only
agentbeats run_agent agent_card.toml --mcp ['http://localhost:9123/sse'] --tool 'tools.py'
```
