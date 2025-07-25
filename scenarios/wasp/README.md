# WASP web agents

This is an implementation of FAIR's WASP web agents built for the AgentBeats environment. The agents are based on the paper [*WASP: Benchmarking Web Agent Security Against Prompt Injection Attacks*](https://arxiv.org/abs/2504.18575).

## Installation

Follow installation steps in order.

### Environment variables
Export the following environment variables

```bash
export DATASET=webarena_prompt_injections
export REDDIT="http://ec2-18-224-83-14.us-east-2.compute.amazonaws.com:9999"
export GITLAB="http://ec2-18-224-83-14.us-east-2.compute.amazonaws.com:8023"
export OPENROUTER_API_KEY=
export OPENROUTER_API_BASE="https://openrouter.ai/api/v1"
```

### Python installations

Verify that you have both python and python3.10 installed (python3.10 must be available through `python3.10` command, if necessary create a symlink).

```bash
python
python3.10
```

### Create virtural environemnt

```bash
python -m venv venv
source venv/bin/activate
pip install agentbeats
```

### Run setup script

Setup script will clone WASP repository and perform virtual environment setup.

```bash
bash setup.sh
```

### Run agents

Run Green, Red and Blue agent.

```bash
bash start-agents.sh
```

### Add agents to the AgentBeats app

Use the web app to add the following agents:

**Blue Agent:**
- Launcher url: http://localhost:9010
- Agent url: http://localhost:9011

**Red Agent:**
- Launcher url: http://localhost:9020
- Agent url: http://localhost:9021

**Green Agent:**
- Launcher url: http://localhost:9030
- Agent url: http://localhost:9031

**Backend Configuration:**
- Backend URL: http://localhost:9000
- MCP URL: http://localhost:9001/sse
