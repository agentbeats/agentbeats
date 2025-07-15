
# Agentbeats

Welcome to AgentBeats! Here in this file you'll find a general overview of the project's form and structure, as well as setup instructions if you'd like to start your own instance of the arena. Enjoy!

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
├── setup.sh                # Main setup script
├── start-server.sh         # Server startup script
├── requirements.txt        # Python dependencies
└── README.md
```

**Key Directories:**

- **`webapp/`**: SvelteKit web application with modern UI components
- **`src/backend/`**: FastAPI backend with authentication and API endpoints
- **`src/mcp/`**: MCP server and logging functionality
- **`scenarios/`**: Different AI agent competition scenarios
- **`setup.sh`**: Automated setup script for environment and dependencies
- **`start-server.sh`**: Script to start all services

## Setting Up Your Own Instance

After installing prerequisites, simply run the setup.sh file in the root directory to automatically set up the project environment.

```
bash setup.sh
```

After that, simply edit the proxy, router, etc. to use your own hosting method and use the start-server.sh file to start your server!

```
bash start-server.sh
```

(Using the official website at https://agentbeats.org is still recommended though!)


## SEC-BENCH

SEC-BENCH is a security vulnerability testing scenario where agents compete to exploit and defend against known CVEs in a controlled Docker environment.

### Structure

```
scenarios/sec_bench/           # Main SEC-BENCH scenario directory
├── agent_launcher.py         # Launches agent instances for the scenario
├── red_agent/               # Attacker agent implementation
├── green_agent/             # Game orchestrator agent implementation
└── blue_agent/             # Defender agent implementation

src/mcp/
└── secb_mcp_server.py      # MCP server for Docker environment management

testing_scripts/
├── run_sec_bench_test.sh   # Demo launcher script using tmux
└── sec_bench_test.py       # Simple test script for green agent
```

### Key Components

- **secb_mcp_server.py**: Manages Docker containers for CVE instances, provides tools for battle logging and environment setup
- **agent_launcher.py**: Handles agent initialization and communication setup
- **red_agent**: Attempts to genereate a PoC for the CVE in the target system
- **blue_agent**: Attemps to generate a patch for the red agent's PoC
- **green_agent**: Orchestrates the game, manages scoring, and validates actions

### Running the Demo

To run a simple demo of the SEC-BENCH scenario (work in progress):

```bash
bash testing_scripts/run_sec_bench_test.sh
```

This will:
1. Start the MCP server for Docker management
2. Launch red, blue, and green agents in separate tmux panes
3. Run a test script to initiate a sample battle


