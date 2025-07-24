#!/usr/bin/env python
"""
Run script for the Agent Beats Backend.
"""
import uvicorn

if __name__ == "__main__":
    print("Starting Agent Beats Backend...")
    print("API will be available at http://0.0.0.0:9000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "src.agentbeats_backend.app:app",
        host="0.0.0.0",
        port=9000,
        reload=True
    )
