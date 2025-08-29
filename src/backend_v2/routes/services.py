# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Path, Query, status, Depends
from typing import Optional, Dict, Any
from ..db import agent_repo, instance_repo
from ..utils.auth import *
from agentbeats.utils.agents import get_agent_card
from ..models.agents import AgentCardAnalysisResponse
from ..utils.agent_utils import check_launcher_status, analyze_agent_card

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


@router.get(
    "/services/agent_card/{agent_id}", tags=["Services"], status_code=status.HTTP_200_OK
)
async def get_agent_card_by_id(
    agent_id: str = Path(..., description="Agent ID"),
):
    """Get agent card information"""
    try:
        agent = agent_repo.get_agent(agent_id)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID {agent_id} not found",
            )

        agent_card = agent.get("agent_card")
        if agent_card is None:
            return {}

        return agent_card

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent card: {str(e)}",
        )


@router.put(
    "/services/agent_card/{agent_id}", tags=["Services"], status_code=status.HTTP_200_OK
)
async def update_agent_card(
    agent_id: str = Path(..., description="Agent ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update agent card information"""
    pass


@router.get("/services/agent_card", tags=["Services"], status_code=status.HTTP_200_OK)
async def fetch_agent_card_by_url(
    agent_url: str = Query(..., description="URL to fetch agent card from"),
):
    """Fetch agent card information from a URL"""
    try:
        agent_card = await get_agent_card(agent_url)

        if not agent_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent card not found at the provided URL",
            )

        return agent_card

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching agent card from URL: {str(e)}",
        )


@router.get(
    "/services/launcher_status", tags=["Services"], status_code=status.HTTP_200_OK
)
async def services_check_launcher_status(
    launcher_url: str = Query(
        ..., description="Launcher base URL to check, e.g. https://host:port"
    )
):
    """Check whether a launcher URL is alive using the agent utils check_launcher_status."""
    try:
        result = await check_launcher_status(launcher_url)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking launcher status: {str(e)}",
        )


@router.post(
    "/services/agent_card_analysis", tags=["Services"], status_code=status.HTTP_200_OK
)
async def services_analyze_agent_card(
    agent_card: Dict[str, Any],
) -> AgentCardAnalysisResponse:
    """Analyze an agent card to detect if the agent is a hosted agent. And parse the participant requirements and battle timeout etc."""
    try:
        analysis = await analyze_agent_card(agent_card)
        return AgentCardAnalysisResponse(**analysis)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing agent card: {str(e)}",
        )