from typing import Optional
from app.modules.rag_system import IRM_RAG
from app.modules.color_engine import ColorEngine
from app.modules.vision_engine import VisionEngine
from app.modules.ai_color_analysis import AIColorAnalysis
from app.modules.agents_system import AgentOrchestrator
from app.modules.digital_twin import DigitalTwinService

class ICAPState:
    def __init__(self) -> None:
        self.rag: Optional[IRM_RAG] = None
        self.color_engine: Optional[ColorEngine] = None
        self.vision_engine: Optional[VisionEngine] = None
        self.ai_analysis: Optional[AIColorAnalysis] = None
        self.agent_orchestrator: Optional[AgentOrchestrator] = None
        self.digital_twin: Optional[DigitalTwinService] = None
