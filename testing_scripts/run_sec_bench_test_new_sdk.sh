#!/bin/bash

# Configuration
PROJECT_DIR=$HOME/agentbeats
SETUP_COMMAND="cd $PROJECT_DIR && source venv/bin/activate"
MAIN_MCP_URL="http://localhost:9001/sse"
DOCKER_MCP_URL="http://localhost:9002/sse"
SESSION_NAME="secbench"

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
pkill -f "python.*secb_mcp_server.py"
pkill -f "python.*agent_launcher.py"
sleep 2  # Give processes time to die

# Kill existing session if it exists
tmux kill-session -t $SESSION_NAME 2>/dev/null

# Create new tmux session
tmux new-session -d -s $SESSION_NAME

# Start MCP server in the first pane
# tmux send-keys -t $SESSION_NAME "$(create_banner 'MCP SERVER')" C-m
# tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && python src/mcp/secb_mcp_server.py" C-m

# Wait for MCP server to start
# echo "Waiting for MCP server to start..."
# sleep 5

# Setup green agent
tmux split-window -v -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME "$(create_banner 'GREEN AGENT')" C-m
tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && agentbeats run_agent scenarios/sec_bench/new_sdk/green_agent/agent_card.toml --tool scenarios/sec_bench/new_sdk/green_agent/tools.py --mcp $MAIN_MCP_URL --mcp $DOCKER_MCP_URL" C-m
tmux select-layout -t $SESSION_NAME even-vertical

# Setup red agent
tmux split-window -v -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME "$(create_banner 'RED AGENT')" C-m
tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && agentbeats run_agent scenarios/sec_bench/new_sdk/red_agent/agent_card.toml --mcp $MAIN_MCP_URL --mcp $DOCKER_MCP_URL" C-m
tmux select-layout -t $SESSION_NAME even-vertical

# Setup blue agent
tmux split-window -v -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME "$(create_banner 'BLUE AGENT')" C-m
tmux send-keys -t $SESSION_NAME "$SETUP_COMMAND && agentbeats run_agent scenarios/sec_bench/new_sdk/blue_agent/agent_card.toml --mcp $MAIN_MCP_URL --mcp $DOCKER_MCP_URL" C-m
tmux select-layout -t $SESSION_NAME even-vertical

# # Create a horizontal pane for the test script
# tmux split-window -h -t $SESSION_NAME
# tmux send-keys -t $SESSION_NAME "$(create_banner 'SEC BENCH TEST')" C-m
# tmux send-keys -t $SESSION_NAME "echo 'Waiting for all agents to initialize...' && sleep 5 && $SETUP_COMMAND && python testing_scripts/sec_bench_test.py" C-m

# Select the first pane
tmux select-pane -t 0

# Attach to the session
tmux attach-session -t $SESSION_NAME

# Optional: Add trap to kill session on script exit
trap "tmux kill-session -t $SESSION_NAME && pkill -f 'python.*secb_mcp_server.py' && pkill -f 'python.*agent_launcher.py'" EXIT