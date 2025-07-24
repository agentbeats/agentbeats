


agentbeats run green_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9030 --agent_host 0.0.0.0 --agent_port 9031 --backend http://localhost:9000 --mcp 'http://localhost:9001/sse' --mcp 'http://localhost:9005/sse' --model_type openai --model_name o4-mini --tool green_agent_tool.py


agentbeats run blue_agent_card.toml --launcher_host 0.0.0.0 --launcher_port 9010 --agent_host 0.0.0.0 --agent_port 9011 --backend http://localhost:9000 --mcp 'http://localhost:9005/sse' --model_type openai --model_name o4-mini