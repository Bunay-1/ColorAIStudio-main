from typing import Optional
from rag_system import IRM_RAG
from color_engine import ColorEngine
from vision_engine import VisionEngine
from ai_color_analysis import AIColorAnalysis
from agents_system import AgentOrchestrator

class ICAPState:
    def __init__(self) -> None:
        self.rag: Optional[IRM_RAG] = None
        self.color_engine: Optional[ColorEngine] = None
        self.vision_engine: Optional[VisionEngine] = None
        self.ai_analysis: Optional[AIColorAnalysis] = None
        self.agent_orchestrator: Optional[AgentOrchestrator] = None
