"""
Agent Service for ICAP Enterprise
==================================
Business logic for AI agent task execution.
"""

import logging
from routers import agents as agents_router

logger = logging.getLogger("Agent_Service")

async def execute_agent_task(request, icap_state):
    """Изпълнява задача чрез AI агент."""
    # We delegate to the router function if it doesn't have Depends,
    # but better to move logic here if it does.
    # For now, let's assume it's just the call to the orchestrator.
    return await icap_state.agent_orchestrator.execute_task(request.get("task"))
