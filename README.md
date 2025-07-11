# README

## Setup Environment

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your OpenAI API key
export OPENAI_API_KEY='your-api-key-here'
```

## How-to run?

### Option 1: Automatic Startup (Recommended)

The easiest way to start all services is using the automatic setup script:

```bash
python setup.py
```

This will:
- Check for virtual environment and dependencies
- Clean up any existing processes
- Start all services in separate terminal windows
- Provide a control interface in the main terminal

**Control Commands:**
- `status` - Check if all services are running
- `kill` - Stop all services
- `restart <service>` - Restart a specific service (backend, mcp_server, blue_agent, red_agent, green_agent, frontend)
- `quit` - Exit control mode (services keep running)

### Option 2: Manual Startup

If you prefer to start services manually:

**Start services manually:**

```bash
# Backend
python -m src.backend.run

# MCP server
python src/logging/testing_mcp.py

# Agents (in separate terminals)
python example_agents/agent_launcher.py --file example_agents/blue_agent/main.py --port 9010
python example_agents/agent_launcher.py --file example_agents/red_agent/main.py --port 9020
python example_agents/agent_launcher.py --file example_agents/green_agent/main.py --port 9030 --mcp-url "http://localhost:9001/sse"

# Frontend (in separate terminal)
cd frontend && npm run dev

# Start game
python testing_scripts/tensortrust_test.py
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