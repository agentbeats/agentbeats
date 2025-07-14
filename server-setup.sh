#!/bin/bash

# AgentBeats Server Setup Script (Background Infrastructure Only)
# Starts all background services/agents for AgentBeats (no frontend/backend/green agents)

set -e

LOG_DIR="logs"
echo -e "\n========== AgentBeats Server Setup =========="
echo "Working directory: $(pwd)"
echo "User: $(whoami)"
echo "Date: $(date)"
echo "Environment:"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:-<not set>}"
echo "  OPENAI_API_BASE: ${OPENAI_API_BASE:-<not set>}"
echo -e "\nCreating log directory: $LOG_DIR"

# Check for required commands
echo "Checking for required commands..."
command -v python3 >/dev/null 2>&1 || { echo "python3 not found!"; exit 1; }

# Only create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
  echo "Creating log directory: $LOG_DIR"
  mkdir "$LOG_DIR"
else
  echo "Log directory already exists: $LOG_DIR"
fi

# Ports to kill (battle_royale: 8000, 8010/8011, 8020/8021, 8030/8031, 8040/8041; tensortrust_mock: 9010/9011, 9020/9021, 9030/9031)
PORTS=(8000 8010 8011 8020 8021 8030 8031 8040 8041 9010 9011 9020 9021 9030 9031)
echo -e "\nKilling any processes on relevant ports..."
for port in "${PORTS[@]}"; do
  pids=$(lsof -ti tcp:$port)
  if [ -n "$pids" ]; then
    echo "Killing process(es) on port $port (PID(s) $pids)"
    for pid in $pids; do
      kill -9 $pid 2>/dev/null || true
    done
  fi
done
echo "Port cleanup complete. Proceeding to Docker and agent startup..."

# Start Docker service manager (battle_royale)
echo -e "\n[1/3] Starting Docker service manager (battle_royale)..."
echo "Using 'docker compose' (plugin)..."
(cd scenarios/battle_royale/docker && sudo docker compose up -d)
echo "Docker service manager step complete."

# Start red agents for battle_royale (3 agents: 8010/8011, 8020/8021, 8030/8031)
echo -e "\n[2/3] Starting battle_royale red agents in background..."
nohup python3 scenarios/battle_royale/agents/agent_launcher.py red_agent --port 8010 > $LOG_DIR/battleroyale_red1_launcher.log 2>&1 &
echo "  Red agent 1 (8010/8011) started."
nohup python3 scenarios/battle_royale/agents/agent_launcher.py red_agent --port 8020 > $LOG_DIR/battleroyale_red2_launcher.log 2>&1 &
echo "  Red agent 2 (8020/8021) started."
nohup python3 scenarios/battle_royale/agents/agent_launcher.py red_agent --port 8030 > $LOG_DIR/battleroyale_red3_launcher.log 2>&1 &
echo "  Red agent 3 (8030/8031) started."
echo "Battle_royale red agents launched."

# Start tensortrust_mock blue and red agents (leave green for manual/tmux)
echo -e "\n[3/3] Starting tensortrust_mock blue and red agents in background..."
nohup python3 scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/blue_agent/main.py --port 9010 > $LOG_DIR/tensortrust_blue_launcher.log 2>&1 &
echo "  Blue agent (9010/9011) started."
nohup python3 scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/red_agent/main.py --port 9020 > $LOG_DIR/tensortrust_red_launcher.log 2>&1 &
echo "  Red agent (9020/9021) started."
echo "Tensortrust_mock blue and red agents launched."

echo -e "\n========== Starting tmux session for manual services (first) =========="
SESSION="agentbeats"
tmux new-session -d -s $SESSION

# Pane 0: Backend
tmux send-keys -t $SESSION:0 "cd $PWD && source venv/bin/activate && python -m src.backend.run" C-m

# Pane 1: Frontend
tmux split-window -h -t $SESSION
 tmux send-keys -t $SESSION:0.1 "cd $PWD/frontend && npm run dev" C-m

# Pane 2: Green Agent (Battle Royale)
tmux split-window -v -t $SESSION:0.0
tmux send-keys -t $SESSION:0.2 "cd $PWD && source venv/bin/activate && python3 scenarios/battle_royale/agents/agent_launcher.py green_agent --port 8040" C-m

# Pane 3: Green Agent (TensorTrust)
tmux split-window -v -t $SESSION:0.1
tmux send-keys -t $SESSION:0.3 "cd $PWD && source venv/bin/activate && python3 scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/green_agent/main.py --port 9030" C-m

tmux select-layout -t $SESSION tiled
echo "Tmux session for manual services started. Attach with: tmux attach -t $SESSION"

echo -e "\n========== Starting background services (docker, agents) =========="
echo -e "\n========== SUMMARY =========="
echo "- Tmux/manual services started first:"
echo "    • Backend (FastAPI)"
echo "    • Frontend (Svelte)"
echo "    • Green Agent (Battle Royale): Controller 8040, Agent 8041"
echo "    • Green Agent (TensorTrust): Controller 9030, Agent 9031"
echo "- Background services:"
echo "    • Docker service manager (battle_royale): scenarios/battle_royale/docker (sudo docker compose)"
echo "    • Battle Royale Red Agents:"
echo "        - Red 1: Controller 8010, Agent 8011 (logs/battleroyale_red1_launcher.log)"
echo "        - Red 2: Controller 8020, Agent 8021 (logs/battleroyale_red2_launcher.log)"
echo "        - Red 3: Controller 8030, Agent 8031 (logs/battleroyale_red3_launcher.log)"
echo "    • TensorTrust Mock Agents:"
echo "        - Blue: Controller 9010, Agent 9011 (logs/tensortrust_blue_launcher.log)"
echo "        - Red: Controller 9020, Agent 9021 (logs/tensortrust_red_launcher.log)"
echo -e "\nLogs are in the $LOG_DIR directory."
echo "Use 'lsof -i :PORT' to check running processes."
echo -e "\n========== SETUP COMPLETE ==========" 