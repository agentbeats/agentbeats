#!/bin/bash

# Configuration
PROJECT_DIR=$HOME/agentbeats
SETUP_COMMAND="cd $PROJECT_DIR && source venv/bin/activate"
CYBERGYM_SETUP_COMMAND="cd scenarios/cybergym"
MAIN_MCP_URL="http://localhost:9001/sse"
DOCKER_MCP_URL="http://localhost:9002/sse"
SESSION_NAME="cybergym"

# Agent ports
GREEN_PORT="8050"
RED_PORT="8060"
BLUE_PORT="8070"

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

# Kill existing processes
echo "Cleaning up existing processes..."
for port in $GREEN_PORT $((GREEN_PORT+1)) $RED_PORT $((RED_PORT+1)) $BLUE_PORT $((BLUE_PORT+1)) 8666 9001 9002; do
    lsof -ti:$port 2>/dev/null | xargs kill -9 2>/dev/null || true
done

sleep 2  # Give processes time to die

# Kill existing session if it exists
tmux kill-session -t $SESSION_NAME 2>/dev/null || true

# Create new tmux session
tmux new-session -d -s $SESSION_NAME

# Start MCP server in the first pane
tmux send-keys -t $SESSION_NAME "$(create_banner 'CyberGym MCP SERVER')" C-m
tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && python -m src.mcp.cybergym_mcp_server" C-m

# Start another MCP server in the second pane
tmux split-window -v -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME "$(create_banner 'Main MCP SERVER')" C-m
tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && python -m src.mcp.mcp_server" C-m

# # Start another MCP server in the third pane
# tmux split-window -v -t $SESSION_NAME
# tmux send-keys -t $SESSION_NAME "$(create_banner 'backend')" C-m
# tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && python -m src.backend.run" C-m

# # Setup green agent
# tmux split-window -h -t $SESSION_NAME
# tmux send-keys -t $SESSION_NAME "$(create_banner 'GREEN AGENT')" C-m
# tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && $CYBERGYM_SETUP_COMMAND && agentbeats run green_agent/agent_card.toml --launcher_host 0.0.0.0 --launcher_port $GREEN_PORT --agent_host 0.0.0.0 --agent_port $((GREEN_PORT+1)) --backend http://localhost:9000 --mcp http://localhost:9001/sse --mcp http://localhost:9002/sse --tool green_agent/tools.py" C-m
# tmux select-layout -t $SESSION_NAME even-vertical

# Setup red agent
tmux split-window -v -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME "$(create_banner 'RED AGENT')" C-m
tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && $CYBERGYM_SETUP_COMMAND && agentbeats run red_agent_card.toml --launcher_host 0.0.0.0 --launcher_port $RED_PORT --agent_host 0.0.0.0 --agent_port $((RED_PORT+1)) --backend http://localhost:9000 --mcp http://localhost:9001/sse --mcp http://localhost:9002/sse" C-m
tmux select-layout -t $SESSION_NAME even-vertical

# # Create a horizontal pane for the test script
# tmux split-window -h -t $SESSION_NAME
# tmux send-keys -t $SESSION_NAME "$(create_banner 'CYBERGYM TEST')" C-m
# tmux send-keys -t $SESSION_NAME "echo 'Waiting for all agents to initialize...' && sleep 5 && $SETUP_COMMAND && python testing_scripts/cybergym_test.py --port $((GREEN_PORT+1))" C-m

# Select the first pane
tmux select-pane -t 0

# Attach to the session
tmux attach-session -t $SESSION_NAME

# Optional: Add trap to kill session on script exit
trap "tmux kill-session -t $SESSION_NAME && pkill -f 'python.*cybergym_mcp_server.py' && pkill -f 'python.*agent_launcher.py'" EXIT