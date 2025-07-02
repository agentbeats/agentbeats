import sys
import os
from datetime import datetime
from agents import function_tool

# Add backend to path so logger can access local backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from backend.db.storage import db

@function_tool(name_override="log_message")
def log_message(message: str) -> str:
    """Log a message to the backend database. Call this to record events, errors, or battle information."""
    try:
        log_entry = {
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'green_agent'
        }
        
        # Write directly to backend database
        db.create('logs', log_entry)
        return f"Successfully logged: {message}"
    except Exception as e:
        return f"Failed to log message: {e}" 