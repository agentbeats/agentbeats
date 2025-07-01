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

# setup agents under A2A protocol
python blue_agent/main.py
python red_agent/main.py
python green_agent/main.py

# start game
python green_agent/unit_test.py
```