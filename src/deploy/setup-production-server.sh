#!/bin/bash

#!/bin/bash
# filepath: /home/lxy98/agentbeats/setup-production-server.sh

# Configuration
SESSION="agentbeats"
PROJECT_DIR="$HOME/agentbeats" # On PRODUCTION SERVER!

echo "Setting up AgentBeats production server..."

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "src" ]; then
    echo "Error: Please run this script from the AgentBeats project root directory"
    exit 1
fi

# Kill existing tmux session if it exists
if tmux has-session -t $SESSION 2>/dev/null; then
    echo "Stopping existing tmux session..."
    tmux kill-session -t $SESSION
fi

# Kill existing pm2 processes
echo "Stopping existing pm2 processes..."
pm2 stop agentbeats-ssr 2>/dev/null || true
pm2 delete agentbeats-ssr 2>/dev/null || true

# Kill processes on AgentBeats ports
echo "Cleaning up ports..."
for prefix in 7 8 9; do
  for x in 0 1 2 3 4 5 6 7 8 9; do
    for port in ${prefix}${x}0 ${prefix}${x}1; do
      pid=$(lsof -ti tcp:$port 2>/dev/null)
      if [ -n "$pid" ]; then
        echo "Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null || true
      fi
    done
  done
done

# Create log directory
LOG_DIR="scenarios/logs"
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory: $LOG_DIR"
    mkdir -p "$LOG_DIR"
fi

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ] || [[ ! "$OPENAI_API_KEY" =~ ^sk ]]; then
    echo "Error: OpenAI API key not set. Set it with: export OPENAI_API_KEY='sk...'"
    exit 1
fi

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Virtual environment found"
fi

# Check frontend dependencies
if [ ! -d "webapp/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd webapp && npm install && cd ..
else
    echo "Frontend dependencies are installed"
fi

# Build frontend
echo "Building frontend..."
cd webapp && npm run build && cd ..

# Start tmux session with backend
echo "Starting backend server..."
tmux new-session -d -s $SESSION -n "backend" "cd $PROJECT_DIR && source venv/bin/activate && python -m src.backend.run"

# Add MCP server window
echo "Starting MCP server..."
tmux new-window -t $SESSION -n "mcp" "cd $PROJECT_DIR && source venv/bin/activate && PYTHONPATH=. python src/mcp/mcp_server.py"

# Add frontend window
echo "Starting frontend..."
tmux new-window -t $SESSION -n "frontend" "cd $PROJECT_DIR/webapp && pm2 start build/index.js --name agentbeats-ssr --no-daemon"

# Add monitoring window
echo "Creating monitoring window..."
tmux new-window -t $SESSION -n "monitor" "cd $PROJECT_DIR && echo 'Monitoring window - useful commands:' && echo 'pm2 list' && echo 'tail -f scenarios/logs/*.log' && echo 'lsof -i :9000' && bash"

# Select backend window
tmux select-window -t $SESSION:backend

echo "Setup complete!"
echo ""
echo "Windows created:"
echo "  backend  - Backend API server"
echo "  mcp      - MCP server"
echo "  frontend - Frontend server via pm2"
echo "  monitor  - System monitoring"
echo ""
echo "To attach: tmux attach -t $SESSION"
echo "To stop all: tmux kill-session -t $SESSION"
echo ""

# Wait for services to start
sleep 3

# Check service status
echo "Checking services..."
if lsof -ti :9000 >/dev/null 2>&1; then
    echo "Backend: Running"
else
    echo "Backend: Not running"
fi

if lsof -ti :9001 >/dev/null 2>&1; then
    echo "MCP: Running"
else
    echo "MCP: Not running"
fi

if pm2 id agentbeats-ssr >/dev/null 2>&1; then
    echo "Frontend: Running"
else
    echo "Frontend: Not running"
fi

echo ""
echo "setup at tmux session: $SESSION"
# read

# # Attach to session
# tmux attach -t $SESSION