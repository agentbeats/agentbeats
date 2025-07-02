#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple HTTP Server for MCP Logger - Hosts the logging tool for remote calls from the green agent.
"""

import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from db.storage import db  # type: ignore

# Create FastAPI app
app = FastAPI(title="MCP Logger Server")

class LogRequest(BaseModel):
    message: str

def log_message_direct(message: str) -> str:
    """Direct logging function without MCP wrapper."""
    try:
        log_entry = {
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'green_agent'
        }
        
        db.create('logs', log_entry)
        return f"Successfully logged: {message}"
    except Exception as e:
        return f"Failed to log message: {e}"

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "MCP Logger Server is running", "status": "ready"}

@app.post("/log")
async def log_endpoint(request: LogRequest):
    """Endpoint to log a message."""
    try:
        result = log_message_direct(request.message)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check for the logging service."""
    return {"status": "healthy", "service": "mcp_logger"}

if __name__ == "__main__":
    print("Starting MCP Logger Server...")
    print("The green agent can call this server to log messages")
    print("Server will be available at: http://localhost:8025")
    uvicorn.run(app, host="0.0.0.0", port=8025) 