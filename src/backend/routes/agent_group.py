from fastapi import APIRouter

router = APIRouter()

@router.get("/agent_group")
async def get_agent_group():
    """List all agent groups (with ownership filtering)"""


@router.post("/agent_group")
async def create_agent_group():
    """Register a new agent group"""


@router.get("/agent_group/{group_id}")
async def get_agent_group_by_id(group_id: str):
    """Get a specific agent group by ID"""


@router.delete("/agent_group/{group_id}")
async def delete_agent_group(group_id: str):
    """Delete a specific agent group by ID"""


@router.get("/agent_group/{group_id}/instances")
async def get_instances_by_group_id(group_id: str):
    """List all instances in a specific agent group by group ID"""


@router.post("/agent_group/{group_id}/instances")
async def create_instances_in_group(group_id: str):
    """Register a new instances in a specific agent group by group ID"""

