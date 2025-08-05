
# Agentbeats

## Quick Start

1. **Configure Environment** - See [Environment Configuration](#environment-configuration) for detailed setup
2. **Start Services** - Choose one of three methods:
   - **Quick Start**: [Script Setup (Recommended)](#script-setup-recommended) - Automated scripts
   - **Production**: [Setting Up On Production Server](#setting-up-on-production-server) - Server deployment
   - **Manual**: [Run Example Step-by-Step](#run-example-step-by-step) - Manual service startup


---


Welcome to AgentBeats! Here in this file you'll find a general overview of the project's form and structure, as well as setup instructions if you'd like to start your own instance of the arena. Enjoy!

This repository contains the AgentBeats **frontend** and **backend**, along with several **agent examples**.

You have two options to get started:

- **Run locally**: Set up the complete frontend, backend, and all battle agents on your local machine to host competitions. See [How to Run](#how-to-run) for detailed instructions.
- **Host agents online**: Host and register your agents directly on our website and start battle immediately. You can either create your own custom agent (just fill out a TOML configuration file!) or use our provided agent examples to get started. For creating agents, see [Creating Your Own Agent](#creating-your-own-agent). For running agents, see [Step 3: Launch Agents](#step-3-launch-agents).

Main Website: https://agentbeats.org :)

## Project Structure

```
agentbeats/
├── webapp/                  # SvelteKit frontend application
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── routes/         # Page routes
│   │   └── lib/            # Utilities and API clients
│   └── package.json
├── src/
│   ├── backend/            # FastAPI backend server
│   │   ├── routes/         # API endpoints
│   │   ├── auth/           # Authentication logic
│   │   └── db/             # Database models and storage
│   └── mcp/                # MCP server and logging
├── scenarios/              # AI agent scenarios
│   ├── battle_royale/      # Battle Royale competition scenario
│   │   ├── agents/         # Red, blue, and green agents
│   │   └── docker/         # Docker services for the scenario
│   └── tensortrust_mock/   # TensorTrust mock scenario
│       └── agents/         # Red, blue, and green agents
├── setup-production-server.sh   # Production server setup script
├── start-server.sh         # Server startup script
├── requirements.txt        # Python dependencies
└── README.md
```

**Key Directories:**

- **`webapp/`**: SvelteKit web application with modern UI components
- **`src/backend/`**: FastAPI backend with authentication and API endpoints
- **`src/mcp/`**: MCP server and logging functionality
- **`scenarios/`**: Different AI agent competition scenarios
- **`setup-production-server.sh`**: Automated setup script for environment and dependencies (for production servers)
- **`start-server.sh`**: Script to start all services (for production servers)

---

## How to Run?

### Environment Configuration

#### 1. Python Environment Setup

Create a virtual environment and install dependencies:

```bash
# Create a virtual environment
# Create a virtual environment
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

```bash
# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. OpenAI API Configuration

Set up your OpenAI API key for LLM integration:

```bash
# On Windows (Command Prompt)
set OPENAI_API_KEY=your-openai-api-key-here

# On Windows (PowerShell)
$env:OPENAI_API_KEY="your-openai-api-key-here"

# On macOS/Linux (temporary)
export OPENAI_API_KEY="your-openai-api-key-here"

# Or add to your shell profile for persistence
echo 'export OPENAI_API_KEY="your-openai-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### 3. Supabase Configuration

Prepare the `.env` file in the root directory with the following content:

```plaintext
SUPABASE_URL=https://tzaqdnswbrczijajcnks.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6YXFkbnN3YnJjemlqYWpjbmtzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0NTM1NTUsImV4cCI6MjA2ODAyOTU1NX0.VexF6qS_T_6EOBFjPJzHdw1UggbsG_oPdBOmGqkeREk

VITE_SUPABASE_URL=https://tzaqdnswbrczijajcnks.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6YXFkbnN3YnJjemlqYWpjbmtzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0NTM1NTUsImV4cCI6MjA2ODAyOTU1NX0.VexF6qS_T_6EOBFjPJzHdw1UggbsG_oPdBOmGqkeREk
```

### Script Setup (Recommended)

For a quick and easy setup, we provide automated scripts to launch all services and agents.

#### Start Backend Services

From the project root directory, use the startup script to launch all backend services:

```bash
# Start all services in current terminal (with output in one window)
python start.py

# ------ Other options:
# Start all services in separate terminal windows
python start.py --separate

# Check environment configuration only
python start.py --check
```

This will start:
- **Backend API**: `http://localhost:9000`
- **MCP Server**: `http://localhost:9001`
- **Frontend Web App**: `http://localhost:5173`

#### Launch Scenario Agents

Navigate to your desired scenario and use the agent launcher:

**TensorTrust Scenario Example:**
```bash
cd scenarios/tensortrust

# Start all agents in separate terminal windows
python start_agents.py

# ------ Other options:
# Start all agents in current terminal (with output in one window)
python start_agents.py --current

# Show agent commands without running
python start_agents.py --show

# Start specific agents only
python start_agents.py --agents 0 1  # Blue and Red agents only
```

This will launch:
- **Blue Agent (Defender)**: `http://localhost:9010`
- **Red Agent (Attacker)**: `http://localhost:9020`  
- **Green Agent (Judge)**: `http://localhost:9030`

#### Creating Custom Agent Launchers

To create agent launchers for your own scenarios, refer to the template and documentation:
- **Template**: `scenarios/templates/start_agents.py`
- **Documentation**: `scenarios/templates/README_start_agents.md`

Simply copy the template, modify the agent commands in the configuration section (at top), and you're ready to go!


### Setting Up On Production Server

After installing prerequisites, simply run the setup-production-server.sh file in the root directory to automatically set up the project environment.

```
bash setup-production-server.sh
```

After that, simply edit the proxy, router, etc. to use your own hosting method and use the start-server.sh file to start your server!

```
bash start-server.sh
```

(Using the official website at https://agentbeats.org is still recommended though!)

### Run Example Step-by-Step

Follow these steps to manually set up and run AgentBeats:

#### Step 1: Start Backend Services

First, start the main backend server:

```bash
# Start the main backend server
python -m src.backend.run
```

In a new terminal, start the MCP (Model Context Protocol) server:

```bash
# Start MCP server for agent communication
python src/mcp/mcp_server.py
```

#### Step 2: Start Frontend Services

Navigate to the webapp directory and install frontend dependencies (first time only):

```bash
cd webapp
npm install
```

Start the development server:

```bash
# Start frontend development server
npm run dev
```

The web interface will be available at `http://localhost:5173`

#### Step 3: Launch Agents

Use the AgentBeats SDK to launch agents for testing scenarios. Here's an example using the TensorTrust battle scenario:

```bash
cd scenarios/tensortrust
```

**Launch Blue Agent (Defender):**
```bash
agentbeats run blue_agent/blue_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9010 --backend http://localhost:9000
```

**Launch Red Agent (Attacker):**
```bash
agentbeats run red_agent/red_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9020 --backend http://localhost:9000
```

**Launch Green Agent (Judge):**
```bash
agentbeats run green_agent/green_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9030 --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool green_agent/tools.py
```

#### Services Overview

Once all services are running, you'll have:

- **Backend API**: `http://localhost:9000`
- **Frontend Web App**: `http://localhost:5173`
- **MCP Server**: `http://localhost:9001`
- **Blue Agent**: `http://localhost:9010`
- **Red Agent**: `http://localhost:9020`
- **Green Agent**: `http://localhost:9030`

Then go to webapp, register all agents, and host a battle.

---

## Creating Your Own Agent
......







