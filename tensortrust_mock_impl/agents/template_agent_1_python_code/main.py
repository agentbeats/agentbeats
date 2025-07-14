import agentbeats as ab

ab_agent = ab.BeatsAgent(__name__)

@ab_agent.tool()
def helloworld_tool():
    """helloworld_tool with a docstring."""
    return "Hello from the agent tool! Your token is !@#$%^&*()"

if __name__ == "__main__":
    ab_agent.load_agent_card("ideal_agent/agent_card.toml")
    ab_agent.add_mcp_server("http://localhost:9123/sse")
    ab_agent.run()
