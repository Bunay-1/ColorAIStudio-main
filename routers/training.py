from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from fastapi import Depends
from utils.models import TrainRequest
from utils.auth import check_permission
from services import training_service

router = APIRouter(prefix="/training", tags=["Model Training"])

@router.post("/start", dependencies=[Depends(check_permission("train"))])
async def train_model(request: TrainRequest, req: Request):
    """Стартира процеса на Fine-tuning."""
    return await training_service.start_training(request, req.app.state)

@router.get("/status")
def get_train_status(req: Request):
    """Връща статуса на обучението."""
    return training_service.get_status(req.app.state)
