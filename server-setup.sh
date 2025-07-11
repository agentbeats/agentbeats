#!/bin/bash

SESSION="agentbeats"
PROJECT_DIR="$HOME/agentbeats"

# Kill any existing session
if tmux has-session -t $SESSION 2>/dev/null; then
  tmux kill-session -t $SESSION
fi

# Start new session and run backend
# Pane 0
cmd_backend="cd $PROJECT_DIR && source venv/bin/activate && python -m src.backend.run"
tmux new-session -d -s $SESSION "$cmd_backend"

# Split and run mcp_server (Pane 1)
cmd_mcp="cd $PROJECT_DIR && source venv/bin/activate && PYTHONPATH=. python src/logging/testing_mcp.py"
tmux split-window -h -t $SESSION "$cmd_mcp"

# Split and run blue_agent (Pane 2)
tmux select-pane -t $SESSION:0.0
tmux split-window -v -t $SESSION "$cmd_backend"
tmux select-pane -t $SESSION:0.2
tmux send-keys -t $SESSION:0.2 "cd $PROJECT_DIR && source venv/bin/activate && python example_agents/agent_launcher.py --file example_agents/blue_agent/main.py --port 9010" C-m

# Split and run red_agent (Pane 3)
tmux select-pane -t $SESSION:0.1
tmux split-window -v -t $SESSION "$cmd_mcp"
tmux select-pane -t $SESSION:0.3
tmux send-keys -t $SESSION:0.3 "cd $PROJECT_DIR && source venv/bin/activate && python example_agents/agent_launcher.py --file example_agents/red_agent/main.py --port 9020" C-m

# Split and run green_agent (Pane 4)
tmux select-pane -t $SESSION:0.2
tmux split-window -v -t $SESSION "cd $PROJECT_DIR && source venv/bin/activate && OPENAI_API_KEY=\$OPENAI_API_KEY python example_agents/agent_launcher.py --file example_agents/green_agent/main.py --port 9030 --mcp-url http://localhost:9001/sse"

# Split and run frontend (Pane 5)
tmux select-pane -t $SESSION:0.3
tmux split-window -v -t $SESSION "cd $PROJECT_DIR/frontend && sudo npm run dev -- --port 80"

# Arrange panes in tiled layout
tmux select-layout -t $SESSION tiled

# Attach to the session
tmux attach -t $SESSION 