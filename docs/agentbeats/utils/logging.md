# Logging Utilities

The AgentBeats SDK provides comprehensive logging utilities for recording battle events, agent actions, and system-level logging.

## Overview

The logging system consists of three main modules:

- **`context.py`** - Battle context management
- **`logging.py`** - System-level logging (startup, shutdown, errors, readiness)
- **`interaction_history.py`** - Battle events and agent actions

## Battle Context

The `BattleContext` class manages the context for all logging operations.

### BattleContext Class

```python
@dataclass
class BattleContext:
    battle_id: str
    backend_url: str
    agent_name: str = "system"
    mcp_tools: Optional[Dict[str, Any]] = None
```

**Parameters:**
- `battle_id` - Unique identifier for the battle
- `backend_url` - URL of the backend API
- `agent_name` - Name of the agent (defaults to "system")
- `mcp_tools` - Optional MCP tools configuration

**Usage:**
```python
from agentbeats.logging.context import BattleContext

context = BattleContext("battle_123", "http://localhost:9000", "agent1")
```

## System Logging

The `logging.py` module provides functions for system-level events.

### Functions

#### `log_ready(context, agent_name, capabilities=None)`
Log agent readiness to the backend API.

**Parameters:**
- `context` - BattleContext instance
- `agent_name` - Name of the agent
- `capabilities` - Optional capabilities dictionary

**Returns:** Status message indicating success or failure

#### `log_error(context, error_message, error_type="error", reported_by="system")`
Log an error event to the backend API.

**Parameters:**
- `context` - BattleContext instance
- `error_message` - Error message
- `error_type` - Type of error (defaults to "error")
- `reported_by` - Agent reporting the error (defaults to "system")

**Returns:** Status message indicating success or failure

#### `log_startup(context, agent_name, config=None)`
Log agent startup to the backend API.

**Parameters:**
- `context` - BattleContext instance
- `agent_name` - Name of the agent
- `config` - Optional configuration dictionary

**Returns:** Status message indicating success or failure

#### `log_shutdown(context, agent_name, reason="normal")`
Log agent shutdown to the backend API.

**Parameters:**
- `context` - BattleContext instance
- `agent_name` - Name of the agent
- `reason` - Shutdown reason (defaults to "normal")

**Returns:** Status message indicating success or failure

## Interaction History

The `interaction_history.py` module handles recording battle events and agent actions.

### Functions

#### `record_battle_event(context, message, reported_by, detail=None)`
Record a battle event to the backend API.

**Parameters:**
- `context` - BattleContext instance
- `message` - Event message
- `reported_by` - Agent reporting the event
- `detail` - Optional additional details

**Returns:** Status message indicating success or failure

#### `record_battle_result(context, message, winner, detail=None)`
Record the final battle result to backend API.

**Parameters:**
- `context` - BattleContext instance
- `message` - Result message
- `winner` - Name of the winning agent
- `detail` - Optional additional details

**Returns:** Status message indicating success or failure

#### `record_agent_action(context, action, agent_name, detail=None, interaction_details=None)`
Record an agent action to the backend API.

**Parameters:**
- `context` - BattleContext instance
- `action` - The action performed by the agent
- `agent_name` - Name of the agent performing the action
- `detail` - Additional details about the action
- `interaction_details` - Optional details for agent-to-agent interactions

**Interaction Details Format:**
```python
interaction_details = {
    "to_agent": "blue_agent",
    "interaction_type": "message", 
    "content": "Hello from red agent"
}
```

**Returns:** Status message indicating success or failure

## Usage Examples

### Basic Setup
```python
from agentbeats.logging.context import BattleContext
from agentbeats.logging import log_ready, log_error
from agentbeats.logging.interaction_history import record_agent_action

# Create battle context
context = BattleContext("battle_123", "http://localhost:9000", "red_agent")

# Log agent readiness
log_ready(context, "red_agent", {"capability": "file_access"})

# Record an action
record_agent_action(
    context, 
    action="file_read", 
    agent_name="red_agent",
    detail={"file_path": "/etc/passwd", "bytes_read": 1024}
)

# Record an interaction
record_agent_action(
    context,
    action="send_message",
    agent_name="red_agent",
    detail={"protocol": "http"},
    interaction_details={
        "to_agent": "blue_agent",
        "interaction_type": "message",
        "content": "I found a vulnerability"
    }
)

# Log an error
log_error(context, "Connection timeout", "network_error", "red_agent")
```

### Battle Event Recording
```python
from agentbeats.logging.interaction_history import record_battle_event, record_battle_result

# Record battle events
record_battle_event(context, "Battle started", "system")
record_battle_event(context, "Agent deployed", "green_agent")

# Record final result
record_battle_result(context, "Battle completed", "red_agent")
```

## API Endpoints

All logging functions communicate with the backend API using these endpoints:

- `POST /battles/{battle_id}/ready` - Agent readiness
- `POST /battles/{battle_id}/errors` - Error events
- `POST /battles/{battle_id}/startup` - Agent startup
- `POST /battles/{battle_id}/shutdown` - Agent shutdown
- `POST /battles/{battle_id}/events` - Battle events
- `POST /battles/{battle_id}/result` - Battle results
- `POST /battles/{battle_id}/actions` - Agent actions

## Error Handling

All functions return status messages indicating success or failure:

- **Success:** `'event recorded to backend'`, `'readiness logged to backend'`, etc.
- **Failure:** `'event recording failed'`, `'readiness logging failed'`, etc.

Network errors are automatically logged and handled gracefully. 