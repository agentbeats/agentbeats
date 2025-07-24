# Template Agent 2 Using CLI

First, fill in `agent_card.toml`.
Then, put all your tools in `tools.py`

Finally, run in this folder:
```
agentbeats run_agent agent_card.toml --mcp ['http://localhost:9123/sse'] --tool 'tools.py'
```
