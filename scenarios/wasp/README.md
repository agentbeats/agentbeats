# WASP web agents

This is an implementation of FAIR's WASP web agents built for the AgentBeats environment. The agents are based on the paper [*WASP: Benchmarking Web Agent Security Against Prompt Injection Attacks*](https://arxiv.org/abs/2504.18575).

## Installation

Follow installation steps in order.

### Environment variables
Export the following environment variables

```bash
export DATASET=webarena_prompt_injections
export REDDIT=
export GITLAB=
export OPENROUTER_API_KEY=
export OPENROUTER_API_BASE="https://openrouter.ai/api/v1"
export RESET_AUTH_TOKEN=
export OPENAI_API_KEY=
```

### Python installations

Verify that you have both python and python3.10 installed (python3.10 must be available through `python3.10` command, if necessary add to PATH or create a symlink).

```bash
python
python3.10
```

### Run setup script

Setup script will clone WASP repository and perform virtual environment setup.

```bash
cd scenarios/wasp
bash setup.sh
```

### Run agents

```bash
pip install agentbeats
# or
pip install -e .
```

```bash
pip install Pillow
```

Run Green, Red and Blue agent.

```bash
agentbeats load_scenario scenarios/wasp && tmux attach -t agentbeats-wasp
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


### Running the Computer use blue agent

To run the computer use blue agent you must either provide the `ANTHROPIC_API_KEY` environmental variable or add the GCP service account with vertex AI credentials into ` ".config/gcloud/agentbeats-235f43dc13fc.json"`. The computer use agent also requires `docker` to be installed.

### Running the GCP server deployment

You can skip this part and just test the pipeline without screenshots visible.

Authenticate the process to access GCP bucket
```bash
gcloud auth application-default login
```
