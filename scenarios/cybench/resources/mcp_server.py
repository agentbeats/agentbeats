import docker
from fastmcp import FastMCP
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


server = FastMCP(
    "Open MCP for Cybench CTF game",
    host="0.0.0.0",
    port=9003,
)

client = docker.from_env()


@server.tool()
def run_terminal_command_in_docker(
    battle_id: str,
    command: str,
    agent_name: str,
) -> str:
    """
    Run a terminal command in the specified docker container for the given battle_id.
    This is for any Red, Blue, or Green agent.
    Logs the command input and output to battle_cmd_history_{battle_id}.json.
    Also, use another MCP server's tool "update_battle_process" to log the command input and the summary of the output.

    Args:
        battle_id: The ID of the battle (Battle ID)
        command: The command to run in the container.
        agent_name: The name of the agent.

    Returns:
        The output of the command.
    """
    logger.info(f"\033[34mExecuting command in container: {command}\033[0m")
    container_name = f"cybench_{battle_id}"
    try:
        container = client.containers.get(container_name)

        # Check if container is running
        if container.status != "running":
            logger.warning(
                f"\033[31mContainer {container_name} is not running, restarting it...\033[0m"
            )
            container.start()

        # Execute command in the running container
        exec_result = container.exec_run(
            ["sh", "-c", command], stdout=True, stderr=True
        )
        output = exec_result.output.decode("utf-8")
        logger.info(f"Output: {output}")
        return output

    except docker.errors.NotFound:
        print(f"Container {container_name} not found, please run a task first")
        return ""
    except Exception as e:
        print(f"Error executing command in container: {e}")
        return ""


if __name__ == "__main__":
    import argparse

    # parse args
    parser = argparse.ArgumentParser(
        description="Run the Sec-Bench MCP server with a configurable port.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9003,
        help="TCP port for the HTTP server to listen on (default: 9003)",
    )
    args = parser.parse_args()
    server.run(
        transport="sse", host="0.0.0.0", port=args.port, log_level="ERROR"
    )
