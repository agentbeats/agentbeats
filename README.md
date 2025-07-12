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

# 5. Install frontend dependencies
cd frontend
npm install
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
python scenarios/agent_launcher.py --file scenarios/tensortrust_mock/blue_agent/main.py --port 9010
python scenarios/agent_launcher.py --file scenarios/tensortrust_mock/red_agent/main.py --port 9020
python scenarios/agent_launcher.py --file scenarios/tensortrust_mock/green_agent/main.py --port 9030 --mcp-url "http://localhost:9001/sse"

# Frontend (in separate terminal)
cd frontend && npm run dev

# Start game
python testing_scripts/tensortrust_test.py
```

## Misc

- SQLite
```
src/backend/db/storage.py
```

- Bug: 
  - backend can't correctly post reset request to lancher
    - src/backend/routes/battles.py : process_battle
  - lancher can't put to backend after reset
    - scenarios/agent_launcher.py

# Production Deployment (auto generated)

## Dependencies
- Python 3.x (with venv)
- Node.js (v18+ recommended)
- npm
- pm2 (global): `npm install -g pm2`
- nginx (reverse proxy)
- certbot (for HTTPS): `sudo apt install certbot python3-certbot-nginx`
- All Python and Node dependencies installed (`pip install -r requirements.txt`, `npm install` in frontend)

## Steps
1. **Clone the repo and set up Python/Node environments.**
2. **Install all dependencies:**
   - Python: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
   - Node: `cd frontend && npm install`
3. **Configure your domain DNS to point to this server.**
4. **Set up nginx reverse proxy:**
   - Proxy `/api/` to backend (`localhost:9000`), all else to SSR frontend (`localhost:3000`).
5. **Obtain HTTPS certificate:**
   - `sudo certbot --nginx -d yourdomain.com`
6. **Run the full stack:**
   - `bash server-setup.sh` (starts backend, agents, SSR frontend with pm2, and reloads nginx)
7. **Access your app at `https://yourdomain.com`**

## Notes
- All build artifacts, logs, and secrets are gitignored.
- pm2 manages the SSR frontend for reliability.
- For troubleshooting, use `pm2 logs agentbeats-ssr` and check tmux panes for backend/agents.

