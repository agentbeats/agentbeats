#!/bin/bash
# Launch script for Battle Royale Green Agent

echo "🚀 Starting Battle Royale Green Agent..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the green_agent directory."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import a2a, uvicorn, requests, agents, openai" 2>/dev/null
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

# Get MCP URL from command line or use default
MCP_URL=${1:-"http://localhost:9001/sse"}

# Start the agent
echo "🎯 Starting Green Agent on port 9031 with MCP URL: $MCP_URL"
python3 main.py --port 9031 --mcp-url "$MCP_URL" 