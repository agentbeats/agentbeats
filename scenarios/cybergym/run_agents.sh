#!/bin/bash

# Configuration
PROJECT_DIR=$HOME/agentbeats
SETUP_COMMAND="cd $PROJECT_DIR && source venv/bin/activate && cd scenarios/cybergym/new_sdk"
SESSION_NAME="cybergym_agents"

# Function to create a fancy banner
create_banner() {
    echo -e "echo '
##############################################
#                                            #
#               $1               
#                                            #
##############################################
'"
}

# Kill existing session if it exists
tmux kill-session -t $SESSION_NAME 2>/dev/null || true

# Create new tmux session
tmux new-session -d -s $SESSION_NAME

# Start Green Agent in the first pane
tmux send-keys -t $SESSION_NAME "$(create_banner 'GREEN AGENT')" C-m
tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && agentbeats run green_agent/agent_card.toml --launcher_host 0.0.0.0 --launcher_port 8050 --agent_host 0.0.0.0 --agent_port 8051 --backend http://localhost:9000 --mcp http://localhost:9001/ss --mcp http://localhost:9002/ss --tool green_agent/tools.py" C-m

# Split window and start Red Agent in the second pane
tmux split-window -v -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME "$(create_banner 'RED AGENT')" C-m
tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && agentbeats run red_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 8060 --agent_host 0.0.0.0 --agent_port 8061 --backend http://localhost:9000 --mcp http://localhost:9001/ss --mcp http://localhost:9002/ss" C-m

# Arrange panes evenly
tmux select-layout -t $SESSION_NAME even-vertical

# Select the first pane
tmux select-pane -t 0

# Attach to the session in the current terminal
tmux attach-session -t $SESSION_NAME

# Optional: Add trap to kill session on script exit
trap "tmux kill-session -t $SESSION_NAME" EXIT


