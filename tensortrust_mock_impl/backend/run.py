#!/usr/bin/env python
"""
Run script for the Agent Beats Backend.
"""
import uvicorn

if __name__ == "__main__":
    print("Starting Agent Beats Backend...")
    print("API will be available at http://localhost:3000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "tensortrust_mock_impl.backend.app:app",
        host="0.0.0.0",
        port=3000,
        reload=True
    )
