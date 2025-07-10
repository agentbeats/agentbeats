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
python -m tensortrust_mock_impl.blue_agent.main
python -m tensortrust_mock_impl.red_agent.main
python -m tensortrust_mock_impl.green_agent.main

# start game
python tensortrust_test.py
```
