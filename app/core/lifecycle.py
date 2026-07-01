import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from app.modules import database
from app.modules.rag_system import IRM_RAG
from app.modules.color_engine import ColorEngine
from app.modules.ai_color_analysis import AIColorAnalysis
from app.modules.vision_engine import VisionEngine
from app.modules.agents_system import AgentOrchestrator
from app.modules.alerting_system import alert_system
from app.core.state import ICAPState
from app.core.ws_manager import ConnectionManager
from app.core.indexer import background_indexer
from app.core.audit import log_to_audit_trail
from utils.logging_config import setup_logging
from utils.config_validator import validate_config, check_service_connectivity
from utils.version import ICAP_VERSION_DISPLAY

load_dotenv()

logger = logging.getLogger("ICAP_API")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.ready = False
    logger.info(f"🚀 Стартиране на ICAP Engine (v{ICAP_VERSION_DISPLAY})...")

    # Initialize Database
    database.init_enterprise_db()

    config_results = validate_config()
    if not config_results["valid"]:
        logger.error("❌ Невалидна конфигурация.")
        if os.environ.get("ICAP_ENVIRONMENT", "production") == "production":
            raise RuntimeError("Невалидна конфигурация в production режим")

    service_status = check_service_connectivity()
    app.state.service_status = service_status

    icap_state = ICAPState()
    icap_state.rag = IRM_RAG(lightweight=(os.environ.get("ICAP_EDGE_MODE") == "1"))
    await icap_state.rag.initialize()
    icap_state.color_engine = ColorEngine()
    icap_state.vision_engine = VisionEngine(triton_url=os.environ.get("TRITON_SERVER_URL"), lightweight=(os.environ.get("ICAP_EDGE_MODE") == "1"))
    icap_state.ai_analysis = AIColorAnalysis()
    icap_state.agent_orchestrator = AgentOrchestrator(icap_state.ai_analysis, icap_state.vision_engine, icap_state.rag)

    app.state.icap = icap_state
    app.state.manager = ConnectionManager()
    app.state.alert_system = alert_system
    app.state.log_to_audit_trail = log_to_audit_trail

    # Background tasks
    indexer_task = asyncio.create_task(background_indexer(app.state.icap, app.state.manager))

    app.state.ready = True
    logger.info("✅ ICAP API стартирането приключи успешно.")

    yield

    # Shutdown
    logger.info("🛑 Спиране на ICAP API...")
    app.state.ready = False
    indexer_task.cancel()
    try:
        await indexer_task
    except asyncio.CancelledError:
        pass

    if icap_state.rag:
        await icap_state.rag.close()
    logger.info("✅ Системата е спряна.")
