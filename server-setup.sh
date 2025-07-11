#!/bin/bash

SESSION="agentbeats"
PROJECT_DIR="$HOME/agentbeats"

# Kill any existing session
if tmux has-session -t $SESSION 2>/dev/null; then
  tmux kill-session -t $SESSION
fi

# Start new session and run backend (Pane 0)
tmux new-session -d -s $SESSION "cd $PROJECT_DIR && source venv/bin/activate && python -m src.backend.run"

# Split horizontally for mcp_server (Pane 1)
tmux split-window -h -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && PYTHONPATH=. python src/logging/testing_mcp.py"

# Split Pane 0 vertically for blue_agent (Pane 2)
tmux select-pane -t $SESSION:0.0
tmux split-window -v -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && python example_agents/agent_launcher.py --file example_agents/blue_agent/main.py --port 9010"

# Split Pane 1 vertically for red_agent (Pane 3)
tmux select-pane -t $SESSION:0.1
tmux split-window -v -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && python example_agents/agent_launcher.py --file example_agents/red_agent/main.py --port 9020"

# Split Pane 2 vertically for green_agent (Pane 4)
tmux select-pane -t $SESSION:0.2
tmux split-window -v -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\$OPENAI_API_KEY python example_agents/agent_launcher.py --file example_agents/green_agent/main.py --port 9030 --mcp-url http://localhost:9001/sse"

# Split Pane 3 vertically for frontend (Pane 5)
tmux select-pane -t $SESSION:0.3
tmux split-window -v -t $SESSION "cd $PROJECT_DIR/frontend && sudo npm run dev -- --port 80"

# Arrange panes in tiled layout
tmux select-layout -t $SESSION tiled

# Attach to the session
tmux attach -t $SESSION 