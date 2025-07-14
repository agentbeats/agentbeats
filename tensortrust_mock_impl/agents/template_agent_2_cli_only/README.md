# Template Agent 2 Using CLI

First, fill in the agent card.
Then, put all your tools in one file

Finally, run:
```
cd tensortrust_mock_impl
agentbeats run_agent \
    agents/template_agent_2_cli_only/agent_card.toml \
    --mcp ['http://localhost:9123/sse'] \
    --tool 'agents/template_agent_2_cli_only/tools.py'
```