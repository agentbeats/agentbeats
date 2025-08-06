# Load environment variables from .env file FIRST, before ANY other imports
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from .routes import agents, battles, websockets
from .a2a_client import a2a_client
from .routes import matches

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Agent Beats Backend")
    from .routes.battles import start_battle_processor
    start_battle_processor()
    yield
    # Shutdown
    logger.info("Shutting down Agent Beats Backend")
    await a2a_client.close()

# Create FastAPI app
app = FastAPI(
    title="Agent Beats Backend API",
    description="Backend for agent registration, battle scheduling and result retrieval",
    version="0.1.1",
    lifespan=lifespan
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
app.include_router(agents.router)
app.include_router(battles.router)
app.include_router(websockets.router)
app.include_router(matches.router)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Add a health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# Run the application if this file is executed directly
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)
