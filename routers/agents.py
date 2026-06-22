from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any, List
import logging
import os
import pandas as pd

router = APIRouter(prefix="/agents", tags=["Multi-Agent System"])
logger = logging.getLogger("IRM_Agents_Router")

class AgentTaskRequest(Dict):
    pass

@router.post("/task")
async def execute_agent_task(request: Dict[str, Any], req: Request):
    """Ендпоинт за изпълнение на комплексни задачи чрез Multi-Agent система."""
    icap = req.app.state.icap
    workflow = request.get("workflow")
    data = request.get("data")
    try:
        results = await icap.agent_orchestrator.execute_workflow(workflow, data)
        return {"workflow": workflow, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit_trail")
async def get_agent_audit_trail():
    """Връща лога с решения на агентите за ISO одит."""
    file_path = "AuditTrail/agent_decisions.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df.tail(50).to_dict(orient="records")
    return []

@router.post("/approve_action")
async def agent_approve_action(data: dict):
    """Ендпоинт за ръчно одобрение на действия на агент (Human-in-the-loop)."""
    agent_name = data.get("agent")
    action = data.get("action")
    operator = data.get("operator", "ADMIN")
    logger.info(f"✅ ОДОБРЕНО: Оператор {operator} одобри действие '{action}' на {agent_name}")
    return {"status": "success", "message": f"Действието е предадено към производствената линия."}
