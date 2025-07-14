# -*- coding: utf-8 -*-
from fastmcp import FastMCP

server = FastMCP("Test MCP for AgentBeast Battle Arena")

@server.tool()
def echo(message: str) -> str:
    """
    Echo the input message with a debug use special string.
    """
    return f"Echo: {message}, token: (*&^%$#@!@1234567890)"


if __name__ == "__main__":
    server.run(
        transport="sse", 
        host="localhost",
        port=9123, 
        log_level="DEBUG")
