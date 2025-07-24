import agentbeats

@agentbeats.tool() # shouldn't be ()
def helloworld_tool():
    """helloworld_tool with a docstring."""
    return "Hello from the agent tool! @#$%^&*()"
