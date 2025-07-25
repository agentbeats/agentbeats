#!/bin/bash

unset TMUX
SESSION="wasp_server_only"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null

# Pane 1: Start backend server
CMD1="source venv/bin/activate && python -m src.backend.run; exec $SHELL"
# Pane 2: Start MCP server
CMD2="source venv/bin/activate && python src/mcp/mcp_server.py; exec $SHELL"
# Pane 3: Frontend (npm install and run dev)
CMD3="cd webapp && npm install && npm run dev; exec $SHELL"

# Start a new tmux session in detached mode with the first pane
tmux new-session -d -s $SESSION "$CMD1"

# Split and run the other commands
tmux split-window -t $SESSION:0 "$CMD2"
tmux select-layout -t $SESSION:0 tiled
tmux split-window -t $SESSION:0 "$CMD3"
tmux select-layout -t $SESSION:0 tiled

# Attach to the session
tmux attach-session -t $SESSION