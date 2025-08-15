# AgentBeats Backend v2

Latest Updates:
+ Added all routes for agents/instances/battles and their reference in orig backend
+ Added all pydantic models that comply to our database table design
+ Add src/backend_v2/database/ folder
  (just delete the JSONStorage class and write a better SQLiteStorage if needed)
+ Transfer all src/backend/agents.py
+ Add src/backend_v2/battle_manager folder 
  (personally, don't put it in routes; please create a class for this and import it)
+ Transfer all src/backend/battles.py

TODO:
+ Transfer all misc (login credential, websockets, auth, mcp, matches)
  + Add automatic MCP prompt hook for all agents

## Quick Start

### 1. Start the Service
```bash
export DEV_LOGIN_MODE=true # linux
python -m src.backend_v2
```

```powershell
$Env:DEV_LOGIN_MODE="true" # windows
python -m src.backend_v2
```

### 2. View API Documentation
After the service starts, visit the following URLs to view API documentation:

- **Swagger UI**: http://localhost:9000/docs
- **Health Check**: http://localhost:9000/health
