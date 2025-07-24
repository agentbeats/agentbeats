# -*- coding: utf-8 -*-
"""
SSH utilities for AgentBeats scenarios.
"""

import paramiko
from typing import Dict, Any, Optional


class SSHClient:
    """SSH client for executing commands on remote hosts."""
    
    def __init__(self, host: str, credentials: Dict[str, Any]):
        self.host = host
        self.credentials = credentials
        self.client: Optional[paramiko.SSHClient] = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the SSH host."""

        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            port = self.credentials.get("port", 22)
            if isinstance(port, str):
                port = int(port)
            
            self.client.connect(
                hostname=self.host,
                port=port,
                username=self.credentials.get("username", "root"),
                password=self.credentials.get("password", ""),
                timeout=10
            )
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to SSH host {self.host}: {str(e)}")
            self.connected = False
            return False
    
    def execute(self, command: str) -> str:
        """Execute a command on the SSH host."""

        if not self.connected:
            if not self.connect():
                return f"Error: Could not connect to {self.host}"
        
        try:
            if self.client is None:
                return f"Error: SSH client not initialized"
            stdin, stdout, stderr = self.client.exec_command(command)
            
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()
            
            result = f"Command: {command}\nExit Status: {exit_status}\n"
            
            if output:
                result += f"Output:\n{output}\n"
            
            if error:
                result += f"Error:\n{error}\n"
            
            if exit_status == 0:
                return f"Success: {result}"
            else:
                return f"Warning: {result}"
                
        except Exception as e:
            return f"SSH Command Error: {str(e)}"
    
    def disconnect(self):
        """Disconnect from the SSH host."""
        if self.client:
            self.client.close()
            self.connected = False
    
    def open_sftp(self):
        """Open an SFTP session."""
        if not self.connected:
            if not self.connect():
                raise Exception(f"Could not connect to {self.host}")
        
        if self.client is None:
            raise Exception("SSH client not initialized")
        
        return self.client.open_sftp()


def create_ssh_connect_tool(agent_instance: Any, default_host: str = "localhost", default_port: int = 22, default_username: str = "root", default_password: str = "") -> Any:
    """Create SSH tool for agent integration."""
    # Note: This function requires the agents module to be available
    # The import is done inside the function to avoid circular imports
    
    try:
        from agents import function_tool
    except ImportError:
        raise ImportError("agents module is required for create_ssh_connect_tool function")
    
    @function_tool(name_override="connect_to_ssh_host")
    def connect_to_ssh_host(host: str = default_host, port: int = default_port, username: str = default_username, password: str = default_password) -> str:
        """Connect to an SSH host."""
        try:
            credentials = {"username": username, "password": password, "port": port}
            ssh_client = SSHClient(host, credentials)
            
            if ssh_client.connect():
                agent_instance.ssh_client = ssh_client
                return f"Successfully connected to SSH host {host}:{port}"
            else:
                return f"Failed to connect to SSH host {host}:{port}"
            
        except Exception as e:
            return f"Failed to connect to SSH host: {str(e)}"
    
    return connect_to_ssh_host


 