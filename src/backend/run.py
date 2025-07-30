#!/usr/bin/env python
"""
Run script for the Agent Beats Backend.
"""
import uvicorn

def main():
    print("Starting Agent Beats Backend...")
    print("API will be available at http://0.0.0.0:9000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=9000,
        reload=True
    )

if __name__ == "__main__":
    main()
