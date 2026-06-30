"""
Training Service for ICAP Enterprise
=====================================
Business logic for model training and fine-tuning.
"""

import sys
import subprocess
import os
import threading
import torch
import logging

logger = logging.getLogger("Training_Service")

async def start_training(request, app_state):
    """Стартира тренировъчен процес."""
    if hasattr(app_state, 'training_process') and app_state.training_process and app_state.training_process.poll() is None:
        return {"message": "Вече тече друг тренировъчен процес."}

    if not torch.cuda.is_available():
        return {"message": "ГРЕШКА: Не е открито NVIDIA GPU (CUDA)."}

    def run_train_thread():
        cmd = [sys.executable, "finetune_unsloth.py", "--epochs", str(request.epochs)]
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        try:
            log_file = open("train_log.txt", "w", encoding="utf-8")
            app_state.training_process = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=log_file)
            app_state.training_process.wait()
        except Exception as e:
            logger.error(f"Грешка в тренировъчния процес: {e}")

    thread = threading.Thread(target=run_train_thread)
    thread.start()
    return {"message": "Обучението е стартирано."}

def get_status(app_state):
    """Връща статуса на текущото обучение."""
    tp = getattr(app_state, 'training_process', None)
    status = "idle"
    if tp:
        status = "running" if tp.poll() is None else ("completed" if tp.returncode == 0 else "failed")
    return {"status": status}
