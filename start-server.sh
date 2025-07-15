#!/bin/bash

# agentbeats server setup script

# colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# functions to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# kill past processes on all agentbeats ports (70xx, 80xx, 90xx)
print_status "Killing processes on AgentBeats ports (70xx, 80xx, 90xx)"

for prefix in 7 8 9; do
  for x in 0 1 2 3 4 5 6 7 8 9; do
    for port in ${prefix}${x}0 ${prefix}${x}1; do
      pid=$(lsof -ti tcp:$port)
      if [ -n "$pid" ]; then
        kill -9 $pid
      fi
    done
  done
done

# set session variables
SESSION="agentbeats"
PROJECT_DIR="$HOME/agentbeats"

# manage background agent logs
LOG_DIR="scenarios/logs"

if [ ! -d "$LOG_DIR" ]; then
  print_status "Creating log directory: $LOG_DIR"
  mkdir "$LOG_DIR"
else
  print_status "Log directory already exists: $LOG_DIR"
fi

# check for openrouter api key
if [ -z "$OPENAI_API_KEY" ] || [[ ! "$OPENAI_API_KEY" =~ ^sk-or-v1 ]]; then
    print_error "OpenRouter API key not set. Set it with: export OPENAI_API_KEY='sk-or-v1-...'"
    exit 1
fi

# check if venv exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    print_error "Virtual environment not found at $PROJECT_DIR/venv"
    exit 1
fi

# start background services using nohup
print_status "Starting background services..."

# mcp server
print_status "Starting MCP server in background..."
nohup bash -c "cd $PROJECT_DIR && source venv/bin/activate && PYTHONPATH=. python src/mcp/mcp_server.py" > $LOG_DIR/mcp_server.log 2>&1 &

# tensortrust_mock blue & red agents
print_status "Starting tensortrust blue agent in background..."
nohup bash -c "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\"$OPENAI_API_KEY\" OPENAI_API_BASE=\"$OPENAI_API_BASE\" && python3 scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/blue_agent/main.py --port 9010" > $LOG_DIR/tensortrust_blue_launcher.log 2>&1 &

print_status "Starting tensortrust red agent in background..."
nohup bash -c "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\"$OPENAI_API_KEY\" OPENAI_API_BASE=\"$OPENAI_API_BASE\" && python3 scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/red_agent/main.py --port 9020" > $LOG_DIR/tensortrust_red_launcher.log 2>&1 &

# battle_royale blue & red agents
print_status "Starting battle royale red agents in background..."
nohup bash -c "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\"$OPENAI_API_KEY\" OPENAI_API_BASE=\"$OPENAI_API_BASE\" && python3 scenarios/battle_royale/agents/agent_launcher.py --file scenarios/battle_royale/agents/red_agent/main.py --port 8010" > $LOG_DIR/battleroyale_red1_launcher.log 2>&1 &
nohup bash -c "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\"$OPENAI_API_KEY\" OPENAI_API_BASE=\"$OPENAI_API_BASE\" && python3 scenarios/battle_royale/agents/agent_launcher.py --file scenarios/battle_royale/agents/red_agent/main.py --port 8020" > $LOG_DIR/battleroyale_red2_launcher.log 2>&1 &
nohup bash -c "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\"$OPENAI_API_KEY\" OPENAI_API_BASE=\"$OPENAI_API_BASE\" && python3 scenarios/battle_royale/agents/agent_launcher.py --file scenarios/battle_royale/agents/red_agent/main.py --port 8030" > $LOG_DIR/battleroyale_red3_launcher.log 2>&1 &

print_status "Starting AgentBeats services with tmux..."

# kill any existing session
if tmux has-session -t $SESSION 2>/dev/null; then
    print_status "Stopping existing session..."
    tmux kill-session -t $SESSION
fi

# start new tmux session with backend
print_status "Starting backend server..."
tmux new-session -d -s $SESSION "cd $PROJECT_DIR && source venv/bin/activate && python -m src.backend.run"

# start tensortrust green agent
print_status "Starting green agent (TensorTrust judge)..."
tmux split-window -v -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\"$OPENAI_API_KEY\" OPENAI_API_BASE=\"$OPENAI_API_BASE\" python scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/green_agent/main.py --port 9030 --mcp-url http://localhost:9001/sse"

# start battle royale green agent
print_status "Starting green agent (Battle Royale judge)..."
tmux select-pane -t $SESSION:0.1
tmux split-window -h -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\"$OPENAI_API_KEY\" OPENAI_API_BASE=\"$OPENAI_API_BASE\" python3 scenarios/battle_royale/agents/agent_launcher.py --file scenarios/battle_royale/agents/green_agent/main.py --port 8040 --mcp-url http://localhost:9001/sse"

# docker startup
print_status "Starting Docker services..."
cd $PROJECT_DIR/scenarios/battle_royale/docker
sudo docker compose up -d
cd $PROJECT_DIR

# start frontend
print_status "Building and starting frontend..."

cd $PROJECT_DIR/webapp && npm run build
cd $PROJECT_DIR/webapp && pm2 start build/index.js --name agentbeats-ssr || pm2 restart agentbeats-ssr

# reload nginx to ensure latest config/certs are active
print_status "Reloading nginx..."
sudo nginx -t && sudo systemctl reload nginx

tmux select-layout -t $SESSION tiled

print_success "All services started successfully!"

print_status "Tips:"
echo "   - Use 'tmux attach -t agentbeats' to reattach to the session"
echo "   - Use 'tmux kill-session -t agentbeats' to stop all services"
echo "   - Press Ctrl+B then D to detach from tmux session"

# attach to the tmux session
tmux attach -t $SESSION 