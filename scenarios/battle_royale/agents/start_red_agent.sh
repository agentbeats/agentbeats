#!/bin/bash
# Launch script for Battle Royale Red Agent

echo "🚀 Starting Battle Royale Red Agent..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the red_agent directory."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import a2a, uvicorn, paramiko, requests, agents, openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Please install requirements:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Set environment variables if not already set
export OPENAI_API_BASE=${OPENAI_API_BASE:-"https://openrouter.ai/api/v1"}
export OPENAI_API_KEY=${OPENAI_API_KEY:-""}

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. Please set it before running the agent."
fi

# Start the agent
echo "🎯 Starting Red Agent on port 9021..."
python3 main.py --port 9021 