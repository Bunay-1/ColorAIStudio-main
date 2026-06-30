"""
RAG Service for ICAP Enterprise
===============================
Business logic for RAG indexing, querying, and knowledge retrieval.
"""

import os
import time
import logging
import httpx
from glob import glob
from utils.circuit_breaker import ollama_breaker
from utils.metrics import rag_documents_indexed_total

logger = logging.getLogger("RAG_Service")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "irm-industrial")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))

async def query_rag(request, icap_state, manager):
    """Извършва RAG диагностика."""
    sources = []
    retrieved_context = ""
    vision_context = ""

    if request.image_data:
        import base64
        temp_img = f"chat_vision_{int(time.time())}.jpg"
        try:
            img_data = base64.b64decode(request.image_data.split(",")[1] if "," in request.image_data else request.image_data)
            with open(temp_img, "wb") as f:
                f.write(img_data)

            defects = icap_state.vision_engine.detect_defects(temp_img)
            micro = icap_state.vision_engine.analyze_micro_defects(temp_img)

            vision_context = f"\n--- VISION AI АНАЛИЗ НА СНИМКАТА ---\n"
            if defects:
                vision_context += f"Открити обекти/дефекти: {', '.join([d['class'] for d in defects])}\n"
            if micro.get('micro_defects_detected'):
                vision_context += f"ViT Детекция: {micro['pattern_recognition']} (Аномалия: {micro['anomaly_score']:.2f})\n"
        except Exception as e:
            logger.error(f"Vision error in chat: {e}")
        finally:
            if os.path.exists(temp_img):
                os.remove(temp_img)

    if request.use_rag:
        retrieved_context, sources = await icap_state.rag.query(request.prompt, filters=request.filters)

    full_context = f"{vision_context}\n{retrieved_context}\n{request.context}".strip()
    if len(full_context) > 4000:
        full_context = full_context[:4000] + "..."

    system_prompt = (
        "Ти си универсален Industrial Intelligence Assistant. Отговаряй кратко и конкретно на български език.\n\n"
        "ПРАВИЛА:\n"
        "- Използвай предоставения контекст (Input) като приоритет.\n"
        "- Давай конкретни технически параметри.\n"
        "- Обърни специално внимание на секцията 'ГРАФ НА ЗНАНИЕТО', за да откриеш логически връзки между процесите.\n"
        "- ВИНАГИ добавяй секция 'ОБОСНОВКА' в края на отговора си, обясняваща защо AI е стигнал до това заключение (Confidence, Ключови фактори).\n"
        "- Избягвай дълги въведения и обяснения."
    )

    full_prompt = f"### System:\n{system_prompt}\n\n### Instruction:\n{request.prompt}\n\n### Input:\n{full_context}\n\n### Response:\n"

    start_time = time.time()
    try:
        async def _call_ollama():
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                ollama_payload = {
                    "model": MODEL_NAME,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": request.temperature}
                }
                response = await client.post(OLLAMA_URL, json=ollama_payload)
                response.raise_for_status()
                return response.json()

        data = await ollama_breaker.call_async(_call_ollama)
        analysis_text = data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        analysis_text = f"[ГРЕШКА] Ollama не е достъпна: {str(e)}"

    return {
        "analysis": analysis_text,
        "sources": sources,
        "timestamp": time.time() - start_time,
        "model": MODEL_NAME
    }

async def index_docs(file_path, icap_state, manager, background_tasks):
    """Индексира документи или директории."""
    supported_extensions = [".pdf", ".docx", ".xlsx", ".xls", ".csv", ".json", ".md", ".html", ".xml", ".tmx", ".zip", ".udb", ".mdb", ".accdb"]

    async def progress_cb(data):
        try:
            await manager.broadcast(data)
        except Exception as e:
            logger.error(f"WS Broadcast error in RAG: {e}")

    if os.path.isdir(file_path):
        files_to_index = []
        for ext in supported_extensions:
            files_to_index.extend(glob(os.path.join(file_path, f"**/*{ext}"), recursive=True))
        files_to_index = list(set(files_to_index))
        for file in files_to_index:
            background_tasks.add_task(icap_state.rag.index_any, file, progress_cb)
        rag_documents_indexed_total.inc(len(files_to_index))
        return {"message": f"Започна индексиране на {len(files_to_index)} файла"}
    else:
        background_tasks.add_task(icap_state.rag.index_any, file_path, progress_cb)
        rag_documents_indexed_total.inc()
        return {"message": f"Започна индексиране на {file_path}"}

async def get_rag_stats(icap_state):
    """Връща статистика за RAG системата."""
    return await icap_state.rag.get_stats()
