#!/bin/bash

unset TMUX
SESSION="agents_session"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null

# Check if required environment variables are set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY environment variable is not set"
    echo "Please set it with: export OPENROUTER_API_KEY=your-api-key"
    exit 1
fi

if [ -z "$OPENROUTER_API_BASE" ]; then
    echo "WARNING: OPENROUTER_API_BASE not set, using default: https://openrouter.ai/api/v1"
    export OPENROUTER_API_BASE=https://openrouter.ai/api/v1
fi

echo "Using OpenRouter API Key: ${OPENROUTER_API_KEY:0:20}..."
echo "Using OpenRouter API Base: $OPENROUTER_API_BASE"

# Pane 4: Launch Blue Agent
CMD1="export OPENROUTER_API_KEY=$OPENROUTER_API_KEY && export OPENROUTER_API_BASE=$OPENROUTER_API_BASE && source venv/bin/activate && agentbeats run blue_agent/blue_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9052 --agent_port 9053 --model_type openrouter --model_name openai/gpt-4o-mini --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool blue_agent/tools.py; exec $SHELL"
# Pane 5: Launch Red Agent
CMD2="export OPENROUTER_API_KEY=$OPENROUTER_API_KEY && export OPENROUTER_API_BASE=$OPENROUTER_API_BASE && source venv/bin/activate && agentbeats run red_agent/red_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9054 --agent_port 9055 --model_type openrouter --model_name openai/gpt-4o-mini --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool red_agent/tools.py; exec $SHELL"
# Pane 6: Launch Green Agent
CMD3="export OPENROUTER_API_KEY=$OPENROUTER_API_KEY && export OPENROUTER_API_BASE=$OPENROUTER_API_BASE && source venv/bin/activate && export RESET_AUTH_TOKEN=$RESET_AUTH_TOKEN && agentbeats run green_agent/green_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9056 --agent_port 9057 --model_type openrouter --model_name openai/gpt-4o-mini --backend http://localhost:9000 --mcp http://localhost:9001/sse --tool green_agent/tools.py; exec $SHELL"

# Start a new tmux session in detached mode with the first pane
tmux new-session -d -s $SESSION "$CMD1"

# Split and run the other commands
tmux split-window -t $SESSION:0 "$CMD2"
tmux select-layout -t $SESSION:0 tiled
tmux split-window -t $SESSION:0 "$CMD3"
tmux select-layout -t $SESSION:0 tiled

# Attach to the session
tmux attach-session -t $SESSION
