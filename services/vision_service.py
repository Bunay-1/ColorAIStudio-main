"""
Vision Service for ICAP Enterprise
==================================
Business logic for computer vision operations.
"""

import os
import time
import cv2
import base64
import logging
from fastapi import HTTPException, UploadFile

logger = logging.getLogger("Vision_Service")

async def analyze_vision(file: UploadFile, generate_map: bool, icap_state, client_host: str):
    """Анализира изображение за дефекти и текстура."""
    content = await file.read()
    temp_path = f"vision_temp_{int(time.time())}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(content)

    try:
        defects = icap_state.vision_engine.detect_defects(temp_path)
        texture = icap_state.vision_engine.analyze_texture(temp_path)
        gloss = icap_state.vision_engine.measure_gloss(temp_path)
        coating = icap_state.vision_engine.detect_uneven_coating(temp_path)

        response = {
            "defects": defects,
            "texture": texture,
            "gloss": gloss,
            "coating_quality": coating,
            "filename": file.filename
        }

        if generate_map:
            heatmap = icap_state.vision_engine.generate_explainability_map(temp_path, defects)
            if heatmap is not None:
                _, buffer_img = cv2.imencode(".jpg", heatmap)
                response["explainability_map"] = base64.b64encode(buffer_img).decode("utf-8")

        return response
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def analyze_micro_vision(file: UploadFile, icap_state):
    """Високопрецизен микро-анализ."""
    file_path = f"AuditTrail/vision_{int(time.time())}_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        return icap_state.vision_engine.analyze_micro_defects(file_path)
    except Exception as e:
        logger.error(f"Грешка при микро-анализ: {e}")
        raise e

async def fuse_vision_views(files: list, icap_state):
    """Обединява изгледи от различни ъгли."""
    temp_paths = []
    try:
        for file in files:
            t_path = f"fusion_temp_{int(time.time())}_{file.filename}"
            with open(t_path, "wb") as b:
                b.write(await file.read())
            temp_paths.append(t_path)

        fused_defects = icap_state.vision_engine.multi_view_fusion(temp_paths)
        return {"fused_defects": fused_defects, "views_analyzed": len(temp_paths)}
    finally:
        for p in temp_paths:
            if os.path.exists(p): os.remove(p)
