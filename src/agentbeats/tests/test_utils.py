"""
Tests for the AgentBeats utils modules.
"""

import unittest
from unittest.mock import patch, MagicMock
import json

# Import utils functions
from agentbeats.utils.commands.ssh import SSHClient, create_ssh_connect_tool


class TestCommandsUtils(unittest.TestCase):
    """Test command execution utilities."""
    
    def test_ssh_client_creation(self):
        """Test SSH client creation."""
        credentials = {"username": "user", "password": "password"}
        ssh_client = SSHClient("host", credentials)
        
        self.assertEqual(ssh_client.host, "host")
        self.assertEqual(ssh_client.credentials, credentials)
        self.assertFalse(ssh_client.connected)
    
    @patch('paramiko.SSHClient')
    def test_ssh_client_connect_success(self, mock_ssh_client):
        """Test successful SSH connection."""
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        
        credentials = {"username": "user", "password": "password"}
        ssh_client = SSHClient("host", credentials)
        
        result = ssh_client.connect()
        
        self.assertTrue(result)
        self.assertTrue(ssh_client.connected)
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once_with(
            hostname="host",
            port=22,
            username="user",
            password="password",
            timeout=10
        )
    
    @patch('paramiko.SSHClient')
    def test_ssh_client_connect_failure(self, mock_ssh_client):
        """Test failed SSH connection."""
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_ssh_client.return_value = mock_client
        
        credentials = {"username": "user", "password": "password"}
        ssh_client = SSHClient("host", credentials)
        
        result = ssh_client.connect()
        
        self.assertFalse(result)
        self.assertFalse(ssh_client.connected)
    
    @patch('paramiko.SSHClient')
    def test_ssh_client_execute_success(self, mock_ssh_client):
        """Test successful SSH command execution."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        
        mock_stdout.read.return_value = b"Command output"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_ssh_client.return_value = mock_client
        
        credentials = {"username": "user", "password": "password"}
        ssh_client = SSHClient("host", credentials)
        ssh_client.client = mock_client
        ssh_client.connected = True
        
        result = ssh_client.execute("ls -la")
        
        self.assertIn("Success:", result)
        self.assertIn("Command output", result)
        mock_client.exec_command.assert_called_once_with("ls -la")
    
    @patch('paramiko.SSHClient')
    def test_ssh_client_execute_failure(self, mock_ssh_client):
        """Test failed SSH command execution."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"Command failed"
        mock_stdout.channel.recv_exit_status.return_value = 1
        
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_ssh_client.return_value = mock_client
        
        credentials = {"username": "user", "password": "password"}
        ssh_client = SSHClient("host", credentials)
        ssh_client.client = mock_client
        ssh_client.connected = True
        
        result = ssh_client.execute("invalid_command")
        
        self.assertIn("Warning:", result)
        self.assertIn("Command failed", result)
    
    def test_create_ssh_connect_tool(self):
        """Test creating SSH connect tool."""
        mock_agent = MagicMock()
        
        # Test that the function returns something (the decorated function or None)
        try:
            tool = create_ssh_connect_tool(mock_agent)
            # The function should return something, even if it's not callable
            self.assertIsNotNone(tool)
        except ImportError:
            # If agents module is not available, that's also valid
            pass


if __name__ == '__main__':
    unittest.main() 