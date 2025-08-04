# AgentBeats Source Code Structure

This directory contains the core source code for the AgentBeats SDK and services.

## Directory Overview

### `agentbeats/` - Core SDK & CLI
The main AgentBeats Python SDK and command-line interface.

- **`cli.py`** - Command-line interface entry point
- **`agent_executor.py`** - Agent execution engine, follow A2A protocol
- **`agent_launcher.py`** - Agent launching and reset management
- **`logging/`** - Logging & recording system with interaction history tracking
- **`utils/`** - Utility modules:
  - `agents/` - A2A communication related utilities
  - `commands/` - SSH and remote command execution
  - `deploy/` - Deployment and scenario management
  - `environment/` - Docker environment handling
  - `static/` - Static file management

### `backend/` - Web API Server
FastAPI-based backend server providing REST API and WebSocket support.

- **`app.py`** - FastAPI application entry point
- **`a2a_client.py`** - Agent-to-agent communication client
- **`auth/`** - Authentication system, with Supabase integration
- **`db/`** - Database, using SQLite
- **`mcp/`** - Frequent used MCP tools and utilities, like battle recording and result reporting
- **`routes/`** - API endpoints
- **`services/`** - Services that frontend may call, like scenario matching and agent role matching

### `mcpcp/` - MCP Control Panel
Model Context Protocol control panel for managing MCP servers.

## Development Workflow

1. **SDK Development**: Work in `agentbeats/` for core functionality
2. **API Development**: Modify `backend/` for server-side features
3. **Frontend Development**: Use `frontend/` for web interface changes. Now we mainly use webapp-v2
4. **MCP Management**: Use `mcpcp/` for MCP tool management