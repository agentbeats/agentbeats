"""
Tests for the AgentBeats logging module.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from agentbeats.logging.context import BattleContext
from agentbeats.logging import log_ready, log_error, log_startup, log_shutdown
from agentbeats.logging.interaction_history import (
    record_battle_event, 
    record_battle_result, 
    record_agent_action
)


class TestBattleContext(unittest.TestCase):
    """Test BattleContext class."""
    
    def test_battle_context_creation(self):
        """Test basic BattleContext creation."""
        context = BattleContext("battle_123", "http://localhost:9000", "agent1")
        
        self.assertEqual(context.battle_id, "battle_123")
        self.assertEqual(context.backend_url, "http://localhost:9000")
        self.assertEqual(context.agent_name, "agent1")
        self.assertIsNone(context.mcp_tools)
    
    def test_battle_context_with_mcp_tools(self):
        """Test BattleContext creation with MCP tools."""
        mcp_tools = {"tool1": "config1", "tool2": "config2"}
        context = BattleContext("battle_123", "http://localhost:9000", "agent1", mcp_tools)
        
        self.assertEqual(context.mcp_tools, mcp_tools)
    
    def test_battle_context_defaults(self):
        """Test BattleContext with default values."""
        context = BattleContext("battle_123", "http://localhost:9000")
        
        self.assertEqual(context.agent_name, "system")
        self.assertIsNone(context.mcp_tools)


class TestSystemLogging(unittest.TestCase):
    """Test system logging functions."""
    
    def setUp(self):
        """Set up test context."""
        self.context = BattleContext("battle_123", "http://localhost:9000", "agent1")
    
    @patch('agentbeats.logging.logging._make_api_request')
    def test_log_ready_success(self, mock_api_request):
        """Test successful log_ready call."""
        mock_api_request.return_value = True
        
        result = log_ready(self.context, "agent1", {"capability": "file_access"})
        
        self.assertEqual(result, 'readiness logged to backend')
        mock_api_request.assert_called_once()
        
        # Check the data sent to API
        call_args = mock_api_request.call_args
        self.assertEqual(call_args[0][0], self.context)
        self.assertEqual(call_args[0][1], "ready")
        
        data = call_args[0][2]
        self.assertEqual(data["event_type"], "agent_ready")
        self.assertEqual(data["agent_name"], "agent1")
        self.assertEqual(data["capabilities"], {"capability": "file_access"})
    
    @patch('agentbeats.logging.logging._make_api_request')
    def test_log_ready_failure(self, mock_api_request):
        """Test failed log_ready call."""
        mock_api_request.return_value = False
        
        result = log_ready(self.context, "agent1")
        
        self.assertEqual(result, 'readiness logging failed')
    
    @patch('agentbeats.logging.logging._make_api_request')
    def test_log_error_success(self, mock_api_request):
        """Test successful log_error call."""
        mock_api_request.return_value = True
        
        result = log_error(self.context, "Connection timeout", "network_error", "agent1")
        
        self.assertEqual(result, 'error logged to backend')
        
        # Check the data sent to API
        call_args = mock_api_request.call_args
        data = call_args[0][2]
        self.assertEqual(data["event_type"], "error")
        self.assertEqual(data["error_type"], "network_error")
        self.assertEqual(data["error_message"], "Connection timeout")
        self.assertEqual(data["reported_by"], "agent1")
    
    @patch('agentbeats.logging.logging._make_api_request')
    def test_log_startup_success(self, mock_api_request):
        """Test successful log_startup call."""
        mock_api_request.return_value = True
        
        config = {"model": "gpt-4", "temperature": 0.7}
        result = log_startup(self.context, "agent1", config)
        
        self.assertEqual(result, 'startup logged to backend')
        
        # Check the data sent to API
        call_args = mock_api_request.call_args
        data = call_args[0][2]
        self.assertEqual(data["event_type"], "agent_startup")
        self.assertEqual(data["agent_name"], "agent1")
        self.assertEqual(data["config"], config)
    
    @patch('agentbeats.logging.logging._make_api_request')
    def test_log_shutdown_success(self, mock_api_request):
        """Test successful log_shutdown call."""
        mock_api_request.return_value = True
        
        result = log_shutdown(self.context, "agent1", "timeout")
        
        self.assertEqual(result, 'shutdown logged to backend')
        
        # Check the data sent to API
        call_args = mock_api_request.call_args
        data = call_args[0][2]
        self.assertEqual(data["event_type"], "agent_shutdown")
        self.assertEqual(data["agent_name"], "agent1")
        self.assertEqual(data["reason"], "timeout")


class TestInteractionHistory(unittest.TestCase):
    """Test interaction history functions."""
    
    def setUp(self):
        """Set up test context."""
        self.context = BattleContext("battle_123", "http://localhost:9000", "agent1")
    
    @patch('agentbeats.logging.interaction_history._make_api_request')
    def test_record_battle_event_success(self, mock_api_request):
        """Test successful record_battle_event call."""
        mock_api_request.return_value = True
        
        detail = {"severity": "high", "category": "security"}
        result = record_battle_event(self.context, "Battle started", "system", detail)
        
        self.assertEqual(result, 'event recorded to backend')
        
        # Check the data sent to API
        call_args = mock_api_request.call_args
        data = call_args[0][2]
        self.assertEqual(data["event_type"], "battle_event")
        self.assertEqual(data["message"], "Battle started")
        self.assertEqual(data["reported_by"], "system")
        self.assertEqual(data["detail"], detail)
    
    @patch('agentbeats.logging.interaction_history._make_api_request')
    def test_record_battle_result_success(self, mock_api_request):
        """Test successful record_battle_result call."""
        mock_api_request.return_value = True
        
        detail = {"score": 95, "duration": "2h30m"}
        result = record_battle_result(self.context, "Battle completed", "red_agent", detail)
        
        self.assertEqual(result, 'battle result recorded: winner=red_agent')
        
        # Check the data sent to API
        call_args = mock_api_request.call_args
        data = call_args[0][2]
        self.assertEqual(data["event_type"], "battle_result")
        self.assertEqual(data["message"], "Battle completed")
        self.assertEqual(data["winner"], "red_agent")
        self.assertEqual(data["detail"], detail)
    
    @patch('agentbeats.logging.interaction_history._make_api_request')
    def test_record_agent_action_success(self, mock_api_request):
        """Test successful record_agent_action call."""
        mock_api_request.return_value = True
        
        detail = {"file_path": "/etc/passwd", "bytes_read": 1024}
        interaction_details = {
            "to_agent": "blue_agent",
            "interaction_type": "message",
            "content": "Hello from red agent"
        }
        
        result = record_agent_action(
            self.context, 
            "send_message", 
            "red_agent", 
            detail, 
            interaction_details
        )
        
        self.assertEqual(result, 'action recorded to backend')
        
        # Check the data sent to API
        call_args = mock_api_request.call_args
        data = call_args[0][2]
        self.assertEqual(data["event_type"], "agent_action")
        self.assertEqual(data["action"], "send_message")
        self.assertEqual(data["agent_name"], "red_agent")
        self.assertEqual(data["detail"], detail)
        self.assertEqual(data["interaction_details"], interaction_details)
    
    @patch('agentbeats.logging.interaction_history._make_api_request')
    def test_record_agent_action_failure(self, mock_api_request):
        """Test failed record_agent_action call."""
        mock_api_request.return_value = False
        
        result = record_agent_action(self.context, "file_read", "red_agent")
        
        self.assertEqual(result, 'action recording failed')


class TestAPIMakeRequest(unittest.TestCase):
    """Test the _make_api_request helper function."""
    
    def setUp(self):
        """Set up test context."""
        self.context = BattleContext("battle_123", "http://localhost:9000", "agent1")
    
    @patch('requests.post')
    def test_make_api_request_success(self, mock_post):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        from agentbeats.logging.interaction_history import _make_api_request
        
        data = {"test": "data"}
        result = _make_api_request(self.context, "test", data)
        
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            "http://localhost:9000/battles/battle_123/test",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
    
    @patch('requests.post')
    def test_make_api_request_failure_status(self, mock_post):
        """Test API request with non-204 status code."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        from agentbeats.logging.interaction_history import _make_api_request
        
        data = {"test": "data"}
        result = _make_api_request(self.context, "test", data)
        
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_make_api_request_network_error(self, mock_post):
        """Test API request with network error."""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        from agentbeats.logging.interaction_history import _make_api_request
        
        data = {"test": "data"}
        result = _make_api_request(self.context, "test", data)
        
        self.assertFalse(result)
        mock_post.assert_called_once()


if __name__ == '__main__':
    unittest.main() 