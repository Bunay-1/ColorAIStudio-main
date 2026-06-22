from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict

class ColorAnalysisRequest(BaseModel):
    lab_sample: List[float]
    lab_standard: List[float]
    method: str = "CIE2000"
    batch_size: float = 100.0
    tolerance: float = 1.0
    illuminant: str = "D65"
    observer: str = "CIE 1931 2 Degree"
    batch_id: str = "BATCH-001"
    operator_id: str = "OPERATOR-01"
    machine_id: str = "MACHINE-01"
    client_id: str = "GENERAL"

class TrendRequest(BaseModel):
    historical_de: List[float]
    tolerance: float = 1.0

class ReasoningRequest(BaseModel):
    prompt: str
    image_data: Optional[str] = None
    context: str = ""
    temperature: float = 0.2
    use_rag: bool = True
    filters: Optional[Dict] = None

class DocumentIndexRequest(BaseModel):
    file_path: str

class TrainRequest(BaseModel):
    dataset: str = "./dataset"
    output: str = "./my_irm_model"
    epochs: int = 3
    batch: int = 2
    lr: float = 2e-4
    lora_r: int = 16
    report_to: str = "none"

class ClientRequirements(BaseModel):
    name: str
    tolerance: float = 1.0
    preferred_method: str = "CIE2000"
    preferred_illuminant: str = "D65"
    notes: Optional[str] = ""

class DiagnosisResponse(BaseModel):
    analysis: str
    sources: List[str] = []
    timestamp: float
    model: str
