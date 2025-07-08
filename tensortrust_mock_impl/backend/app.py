import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routes import agents, battles, users
from .a2a_client import a2a_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agent Beats Backend API",
    description="Backend for agent registration, battle scheduling and result retrieval",
    version="0.1.1"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, tags=["Agents"])
app.include_router(battles.router, tags=["Battles"])
app.include_router(users.router, tags=["Users"])

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Agent Beats Backend")
    # Start the battle queue processor
    from .routes.battles import start_battle_processor
    start_battle_processor()
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Agent Beats Backend")
    # Close the A2A client session
    await a2a_client.close()
    
# Add a health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# Run the application if this file is executed directly
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)
