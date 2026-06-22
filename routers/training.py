from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
import sys
import subprocess
import os
import threading
import time
import torch
from fastapi import Depends
from utils.models import TrainRequest
from utils.auth import check_permission

router = APIRouter(prefix="/training", tags=["Model Training"])

@router.post("/start", dependencies=[Depends(check_permission("train"))])
async def train_model(request: TrainRequest, req: Request):
    """Стартира процеса на Fine-tuning."""
    # This logic still needs access to a global/shared training_process variable
    # We'll assume it's in req.app.state
    if hasattr(req.app.state, 'training_process') and req.app.state.training_process and req.app.state.training_process.poll() is None:
        return {"message": "Вече тече друг тренировъчен процес."}

    def run_train_thread():
        cmd = [sys.executable, "finetune_unsloth.py", "--epochs", str(request.epochs)]
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        log_file = open("train_log.txt", "w", encoding="utf-8")
        req.app.state.training_process = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=log_file)
        req.app.state.training_process.wait()

    if not torch.cuda.is_available():
        return {"message": "ГРЕШКА: Не е открито NVIDIA GPU (CUDA)."}

    thread = threading.Thread(target=run_train_thread)
    thread.start()
    return {"message": "Обучението е стартирано."}

@router.get("/status")
def get_train_status(req: Request):
    tp = getattr(req.app.state, 'training_process', None)
    status = "idle"
    if tp:
        status = "running" if tp.poll() is None else ("completed" if tp.returncode == 0 else "failed")
    return {"status": status}
