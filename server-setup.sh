#!/bin/bash

# AgentBeats Server Setup Script
# This script starts all AgentBeats services in a tmux session
# Supports both OpenAI and OpenRouter APIs

SESSION="agentbeats"
PROJECT_DIR="$HOME/agentbeats"

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY environment variable is not set!"
    echo "   Set it with: export OPENAI_API_KEY='your-api-key-here'"
    echo "   For OpenRouter: export OPENAI_API_BASE='https://openrouter.ai/api/v1'"
    exit 1
fi

# Set default API base if not provided
if [ -z "$OPENAI_API_BASE" ]; then
    export OPENAI_API_BASE="https://api.openai.com/v1"
    echo "ℹ️  Using default OpenAI API base: $OPENAI_API_BASE"
else
    echo "ℹ️  Using custom API base: $OPENAI_API_BASE"
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "❌ ERROR: Virtual environment not found at $PROJECT_DIR/venv"
    echo "   Please create it first:"
    echo "   cd $PROJECT_DIR"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo "🚀 Starting AgentBeats services with tmux..."

# Kill any existing session
if tmux has-session -t $SESSION 2>/dev/null; then
    echo "🛑 Stopping existing session..."
    tmux kill-session -t $SESSION
fi

# Start new session and run backend (Pane 0)
echo "📡 Starting backend server..."
tmux new-session -d -s $SESSION "cd $PROJECT_DIR && source venv/bin/activate && python -m src.backend.run"

# Split horizontally for mcp_server (Pane 1)
echo "📊 Starting MCP logging server..."
tmux split-window -h -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && PYTHONPATH=. python src/logging/testing_mcp.py"

# Split Pane 0 vertically for blue_agent (Pane 2)
echo "🔵 Starting blue agent (defender)..."
tmux select-pane -t $SESSION:0.0
tmux split-window -v -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\$OPENAI_API_KEY OPENAI_API_BASE=\$OPENAI_API_BASE python scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/blue_agent/main.py --port 9010"

# Split Pane 1 vertically for red_agent (Pane 3)
echo "🔴 Starting red agent (attacker)..."
tmux select-pane -t $SESSION:0.1
tmux split-window -v -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\$OPENAI_API_KEY OPENAI_API_BASE=\$OPENAI_API_BASE python scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/red_agent/main.py --port 9020"

# Split Pane 2 vertically for green_agent (Pane 4)
echo "🟢 Starting green agent (judge)..."
tmux select-pane -t $SESSION:0.2
tmux split-window -v -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\$OPENAI_API_KEY OPENAI_API_BASE=\$OPENAI_API_BASE python scenarios/tensortrust_mock/agent_launcher.py --file scenarios/tensortrust_mock/green_agent/main.py --port 9030 --mcp-url http://localhost:9001/sse"

# --- Frontend SSR build and start (no tmux pane needed, runs with pm2) ---
echo "🌐 Building and starting frontend..."
# Build the SSR frontend (safe to run even if already built)
cd $PROJECT_DIR/frontend && npm run build
# Start or restart the SSR server with pm2
cd $PROJECT_DIR/frontend && pm2 start build/index.js --name agentbeats-ssr || pm2 restart agentbeats-ssr
# --- End frontend SSR ---

# Reload nginx to ensure latest config/certs are active
echo "🔄 Reloading nginx..."
sudo nginx -t && sudo systemctl reload nginx

# Arrange panes in tiled layout
tmux select-layout -t $SESSION tiled

echo "✅ All services started successfully!"
echo "📋 Service Summary:"
echo "   • Backend API: http://localhost:9000"
echo "   • MCP Server: http://localhost:9001"
echo "   • Blue Agent Controller: http://localhost:9010"
echo "   • Blue Agent: http://localhost:9011"
echo "   • Red Agent Controller: http://localhost:9020"
echo "   • Red Agent: http://localhost:9021"
echo "   • Green Agent Controller: http://localhost:9030"
echo "   • Green Agent: http://localhost:9031"
echo "   • Frontend: http://localhost:5173"
echo ""
echo "💡 Tips:"
echo "   • Use 'tmux attach -t agentbeats' to reattach to the session"
echo "   • Use 'tmux kill-session -t agentbeats' to stop all services"
echo "   • Press Ctrl+B then D to detach from tmux session"

# Attach to the session
tmux attach -t $SESSION 