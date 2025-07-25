# -*- coding: utf-8 -*-
"""
Battle Royale Red Agent Tools
Flexible framework for agents to create their own web service strategies.
"""

import json
import time
import agentbeats as ab
from typing import Dict, Any, Optional, Tuple

# Import SDK utilities
from agentbeats.utils.commands import SSHClient

# Import logging utilities
from agentbeats.logging import BattleContext, record_agent_action, record_battle_event, log_error

# Minimal global state for agent compatibility
agent_id = None
ssh_client = None
battle_context = None

@ab.tool
def handle_battle_start(battle_info_json: str) -> str:
    """Handle battle start message from green agent."""
    try:
        battle_info = json.loads(battle_info_json)
        
        # Extract battle information
        battle_id = battle_info.get("battle_id")
        agent_id_value = battle_info.get("agent_id")
        ssh_credentials = battle_info.get("ssh_credentials")
        backend_url = battle_info.get("backend_url", "http://localhost:8000")
        
        global agent_id, battle_context
        
        if not agent_id_value:
            print("ERROR: No agent ID provided in battle info")
            return "No agent ID provided in battle info"
        
        # Store agent ID globally for other functions
        agent_id = agent_id_value
        print(f"Agent ID set to: {agent_id}")
        
        # Initialize battle context for logging
        battle_context = BattleContext(
            battle_id=battle_id,
            backend_url=backend_url,
            agent_name=agent_id
        )
        
        # Log battle start
        record_battle_event(battle_context, f"Red agent {agent_id} starting battle", agent_id, {
            "battle_id": battle_id,
            "agent_type": "red_agent"
        })
        
        # Connect to battle arena
        if ssh_credentials:
            host = ssh_credentials.get("host")
            port = ssh_credentials.get("port")
            username = ssh_credentials.get("username")
            password = ssh_credentials.get("password")
            
            if all([host, port, username, password]):
                client = connect_to_battle_arena(host, port, username, password)
                if client:
                    # Store SSH client globally for other functions
                    global ssh_client
                    ssh_client = client
                    
                    # Log successful connection
                    record_agent_action(battle_context, "ssh_connection_established", agent_id, {
                        "host": host,
                        "port": port,
                        "username": username
                    })
                    
                    return f"Battle started successfully! Connected to {username}@{host}:{port}. Ready to deploy web service strategy."
                else:
                    log_error(battle_context, "Failed to connect to battle arena", "ssh_connection_error", agent_id)
                    return "Failed to connect to battle arena"
        
        return "Battle start message processed"
        
    except Exception as e:
        error_msg = f"Failed to handle battle start: {str(e)}"
        if battle_context:
            log_error(battle_context, error_msg, "battle_start_exception", agent_id or "red_agent")
        return error_msg

def connect_to_battle_arena(host: str, port: int, username: str, password: str) -> Optional[SSHClient]:
    """Connect to the battle arena via SSH. Returns SSHClient if successful, None if failed."""
    try:
        print(f"Connecting to battle arena at {username}@{host}:{port}")
        
        # Create SSH client using the SDK
        credentials = {
            "username": username,
            "password": password,
            "port": port
        }
        
        ssh_client = SSHClient(host, credentials)
        connection_successful = ssh_client.connect()
        
        if connection_successful:
            print("Successfully connected to battle arena")
            return ssh_client
        else:
            print("SSH connection failed")
            return None
        
    except Exception as e:
        print(f"Failed to connect to battle arena: {str(e)}")
        return None

def execute_ssh_command(command: str, ssh_client: SSHClient) -> str:
    """Execute a command on the battle arena via SSH."""
    try:
        if ssh_client is None:
            return "SSH client not provided"
        
        print(f"Executing SSH command: {command}")
        
        result = ssh_client.execute(command)
        
        if result.startswith("Success:"):
            print("SSH command executed successfully")
            return result
        else:
            print("SSH command failed")
            return result
            
    except Exception as e:
        print(f"SSH command error: {str(e)}")
        return f"SSH command error: {str(e)}"

@ab.tool
def deploy_custom_web_service(service_code: str, port: int = 80, filename: str = "custom_service.py") -> str:
    """Deploy a custom web service with agent-generated code."""
    try:
        global agent_id, ssh_client, battle_context
        
        if ssh_client is None:
            return "SSH client not provided"
        
        if not agent_id:
            return "Agent ID not provided"
        
        print(f"Deploying custom web service on port {port}")
        
        # Log deployment attempt
        if battle_context:
            record_agent_action(battle_context, "deploy_web_service_attempt", agent_id, {
                "port": port,
                "filename": filename,
                "code_length": len(service_code)
            })
        
        # Clean up any existing services on the target port
        print(f"Cleaning up any existing services on port {port}...")
        execute_ssh_command(f"fuser -k {port}/tcp 2>/dev/null || true", ssh_client)
        execute_ssh_command(f"pkill -f '{filename}' 2>/dev/null || true", ssh_client)
        time.sleep(2)  # Wait for cleanup
        
        # Write custom service code to remote server
        sftp = ssh_client.open_sftp()
        
        # Create service file with the custom code
        with sftp.file(f'/tmp/{filename}', 'w') as f:
            f.write(service_code)
        
        # Make it executable
        execute_ssh_command(f"chmod +x /tmp/{filename}", ssh_client)
        
        # Start the service in background
        execute_ssh_command(f"nohup python3 /tmp/{filename} > /tmp/{filename}.log 2>&1 &", ssh_client)
        
        # Wait a moment for service to start
        time.sleep(3)
        
        # Check if service is running
        result = execute_ssh_command(f"curl -s http://localhost:{port}", ssh_client)
        print(f"Curl result: '{result}'")
        
        if result and not result.startswith("curl:"):
            print(f"Custom web service deployed and running on port {port}")
            
            # Log successful deployment
            if battle_context:
                record_agent_action(battle_context, "web_service_deployed", agent_id, {
                    "port": port,
                    "filename": filename,
                    "status": "running"
                })
            
            return f"Custom web service deployed and running on port {port}"
        else:
            # Check the log for errors
            log_result = execute_ssh_command(f"cat /tmp/{filename}.log", ssh_client)
            print(f"Service log: {log_result}")
            
            # Log deployment failure
            if battle_context:
                log_error(battle_context, f"Web service deployment failed on port {port}", "deployment_error", str(agent_id or "red_agent"))
            
            return f"Custom web service deployment may have failed. Check logs: {log_result}"
            
    except Exception as e:
        error_msg = f"Error deploying custom web service: {str(e)}"
        print(error_msg)
        
        # Log deployment error
        if battle_context:
            log_error(battle_context, error_msg, "deployment_exception", str(agent_id or "red_agent"))
        
        return error_msg

@ab.tool
def execute_custom_strategy(strategy_commands: str) -> str:
    """Execute a custom strategy with multiple commands."""
    try:
        global ssh_client, battle_context, agent_id
        
        if ssh_client is None:
            return "SSH client not provided"
        
        print("Executing custom strategy")
        
        # Log strategy execution
        if battle_context:
            record_agent_action(battle_context, "execute_custom_strategy", str(agent_id or "red_agent"), {
                "command_count": len(strategy_commands.split('\n')),
                "strategy_length": len(strategy_commands)
            })
        
        # Split commands by newlines and execute each
        commands = [cmd.strip() for cmd in strategy_commands.split('\n') if cmd.strip()]
        
        results = []
        for command in commands:
            try:
                result = execute_ssh_command(command, ssh_client)
                results.append(f"Command '{command}': {result}")
            except Exception as e:
                results.append(f"Command '{command}' failed: {str(e)}")
        
        # Log strategy completion
        if battle_context:
            record_agent_action(battle_context, "custom_strategy_completed", str(agent_id or "red_agent"), {
                "commands_executed": len(commands),
                "successful_commands": len([r for r in results if "failed" not in r])
            })
        
        return f"Strategy execution completed:\n" + "\n".join(results)
        
    except Exception as e:
        error_msg = f"Error executing custom strategy: {str(e)}"
        print(error_msg)
        
        # Log strategy error
        if battle_context:
            log_error(battle_context, error_msg, "strategy_execution_error", str(agent_id or "red_agent"))
        
        return error_msg

@ab.tool
def check_port_status(port: int = 80) -> str:
    """Check if a specific port is in use and what's running on it."""
    try:
        global ssh_client
        
        if ssh_client is None:
            return "SSH client not provided"
        
        print(f"Checking status of port {port}")
        
        # Check what's using the port
        port_check = execute_ssh_command(f"lsof -i :{port} 2>/dev/null || echo 'Port {port} is free'", ssh_client)
        
        # Try to connect to the port
        curl_result = execute_ssh_command(f"curl -s -m 5 http://localhost:{port} 2>/dev/null || echo 'No response from port {port}'", ssh_client)
        
        return f"Port {port} status:\nPort usage: {port_check}\nService response: {curl_result}"
        
    except Exception as e:
        print(f"Error checking port status: {str(e)}")
        return f"Error checking port status: {str(e)}"

@ab.tool
def find_available_port(start_port: int = 80, max_port: int = 90) -> str:
    """Find an available port in the specified range."""
    try:
        global ssh_client
        
        if ssh_client is None:
            return "SSH client not provided"
        
        print(f"Finding available port between {start_port} and {max_port}")
        
        for port in range(start_port, max_port + 1):
            result = execute_ssh_command(f"lsof -i :{port} 2>/dev/null || echo 'free'", ssh_client)
            if "free" in result:
                print(f"Found available port: {port}")
                return f"Available port found: {port}"
        
        return f"No available ports found in range {start_port}-{max_port}"
        
    except Exception as e:
        print(f"Error finding available port: {str(e)}")
        return f"Error finding available port: {str(e)}"

@ab.tool
def sabotage_competitors(sabotage_commands: str) -> str:
    """Execute sabotage commands against competitors."""
    try:
        global ssh_client, battle_context, agent_id
        
        if ssh_client is None:
            return "SSH client not provided"
        
        print("Executing sabotage strategy")
        
        # Log sabotage attempt
        if battle_context:
            record_agent_action(battle_context, "sabotage_attempt", str(agent_id or "red_agent"), {
                "command_count": len(sabotage_commands.split('\n')),
                "strategy_type": "sabotage"
            })
        
        # Split commands by newlines and execute each
        commands = [cmd.strip() for cmd in sabotage_commands.split('\n') if cmd.strip()]
        
        results = []
        for command in commands:
            try:
                result = execute_ssh_command(command, ssh_client)
                results.append(f"Sabotage command '{command}': {result}")
            except Exception as e:
                results.append(f"Sabotage command '{command}' failed: {str(e)}")
        
        # Log sabotage completion
        if battle_context:
            record_agent_action(battle_context, "sabotage_completed", str(agent_id or "red_agent"), {
                "commands_executed": len(commands),
                "successful_sabotages": len([r for r in results if "failed" not in r])
            })
        
        return f"Sabotage execution completed:\n" + "\n".join(results)
        
    except Exception as e:
        error_msg = f"Error executing sabotage: {str(e)}"
        print(error_msg)
        
        # Log sabotage error
        if battle_context:
            log_error(battle_context, error_msg, "sabotage_error", str(agent_id or "red_agent"))
        
        return error_msg

@ab.tool
def monitor_battlefield() -> str:
    """Get comprehensive battlefield information."""
    try:
        global ssh_client
        
        if ssh_client is None:
            return "SSH client not provided"
        
        print("Monitoring battlefield")
        
        # Get various system information
        commands = [
            "ps aux | grep -E '(python|http|nginx|apache)' | grep -v grep",
            "netstat -tlnp | grep :80",
            "lsof -i :80",
            "curl -s http://localhost:80 2>/dev/null || echo 'No service on port 80'",
            "df -h /tmp",
            "free -h"
        ]
        
        results = []
        for command in commands:
            try:
                result = execute_ssh_command(command, ssh_client)
                results.append(f"Command '{command}':\n{result}")
            except Exception as e:
                results.append(f"Command '{command}' failed: {str(e)}")
        
        return f"Battlefield status:\n" + "\n".join(results)
        
    except Exception as e:
        print(f"Error monitoring battlefield: {str(e)}")
        return f"Error monitoring battlefield: {str(e)}"

@ab.tool
def reset_agent_state() -> str:
    """Reset the agent's state and disconnect from SSH."""
    try:
        global agent_id, ssh_client, battle_context
        
        print("Resetting agent state")
        
        # Log reset attempt
        if battle_context:
            record_agent_action(battle_context, "agent_reset_attempt", str(agent_id or "red_agent"), {
                "reset_type": "full_state_reset"
            })
        
        # Close SSH connection if open
        if ssh_client:
            try:
                ssh_client.disconnect()
                print("SSH connection closed")
            except Exception as e:
                print(f"Error closing SSH connection: {str(e)}")
                if battle_context:
                    log_error(battle_context, f"Error closing SSH connection: {str(e)}", "ssh_disconnect_error", str(agent_id or "red_agent"))
        
        # Reset global state
        agent_id = None
        ssh_client = None
        battle_context = None
        
        print("Agent state reset complete")
        return "Agent state reset complete"
        
    except Exception as e:
        error_msg = f"Error resetting agent state: {str(e)}"
        print(error_msg)
        
        # Log reset error
        if battle_context:
            log_error(battle_context, error_msg, "reset_error", str(agent_id or "red_agent"))
        
        return error_msg 