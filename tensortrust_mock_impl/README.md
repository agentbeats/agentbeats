# README

## How-to run?

Install environment:

```
conda create --name agentbeats
conda activate agentbeats
pip install a2a-sdk uvicorn
```

Run a game:

```
cd tensortrust_mock_impl

# setup backend mcp server
python backend/server_mcp.py

# setup agents under A2A protocol
python agent_launcher.py --file blue_agent/main.py  --port 8000
python agent_launcher.py --file red_agent/main.py   --port 9000
python agent_launcher.py --file green_agent/main.py --port 10000

# start game
python mock_game.py
```