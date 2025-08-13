# -*- coding: utf-8 -*-

import uvicorn

from fastapi import FastAPI
from .routes import agents, agent_instances, battles, misc


app = FastAPI(
    title="Agent Beats Backend API",
    description="Backend for agent registration, battle scheduling and result retrieval",
    version="1.0.0",
)
app.include_router(agents.router)
app.include_router(agent_instances.router)
app.include_router(battles.router)
app.include_router(misc.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
