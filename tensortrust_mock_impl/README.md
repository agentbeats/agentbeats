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
# backend
python -m tensortrust_mock_impl.backend.run

cd tensortrust_mock_impl

# setup backend mcp server
python logging/testing_mcp.py

# setup agents under A2A protocol
python agent_launcher.py --file blue_agent/main.py  --port 9010
python agent_launcher.py --file red_agent/main.py   --port 9020
python agent_launcher.py --file green_agent/main.py --port 9030 --mcp-url "http://localhost:9001/sse"

# start game
python tensortrust_test.py
```

## Misc

- SQLite
```
backend/db/storage.py
```

- Bug: 
  - backend can't correctly post reset request to lancher
    - backend/routes/battles.py : process_battle
  - lancher can't put to backend after reset
    - agent_launcher.py