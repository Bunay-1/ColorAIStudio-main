from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ColorAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lab_sample: List[float] = Field(..., min_length=3, max_length=3)
    lab_standard: List[float] = Field(..., min_length=3, max_length=3)
    method: str = Field("CIE2000")
    batch_size: float = Field(100.0, gt=0)
    tolerance: float = Field(1.0, gt=0)
    illuminant: str = Field("D65")
    observer: str = Field("CIE 1931 2 Degree")
    batch_id: str = Field("BATCH-001", min_length=1)
    operator_id: str = Field("OPERATOR-01", min_length=1)
    machine_id: str = Field("MACHINE-01", min_length=1)
    client_id: str = Field("GENERAL", min_length=1)

    @field_validator("lab_sample", "lab_standard")
    @classmethod
    def validate_lab_coordinates(cls, value: List[float]) -> List[float]:
        if len(value) != 3:
            raise ValueError("L*a*b* координатите трябва да имат точно 3 стойности.")
        L, a, b = value
        if not (0 <= L <= 100):
            raise ValueError("L* координатата трябва да е между 0 и 100.")
        if not (-128 <= a <= 127) or not (-128 <= b <= 127):
            raise ValueError("a* и b* координатите трябва да са между -128 и 127.")
        return [float(L), float(a), float(b)]

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        allowed = {"CIE76", "CIE94", "CIE2000", "CMC"}
        if value not in allowed:
            raise ValueError(f"Методът трябва да е един от {sorted(allowed)}.")
        return value

class TrendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    historical_de: List[float] = Field(..., min_length=3)
    tolerance: float = Field(1.0, gt=0)

    @field_validator("historical_de")
    @classmethod
    def validate_history(cls, value: List[float]) -> List[float]:
        if any(not isinstance(x, (int, float)) for x in value):
            raise ValueError("Всички стойности в historical_de трябва да са числа.")
        return [float(x) for x in value]

class ReasoningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., min_length=1)
    image_data: Optional[str] = None
    context: str = Field("", max_length=4000)
    temperature: float = Field(0.2, ge=0.0, le=1.0)
    use_rag: bool = True
    filters: Optional[Dict[str, Any]] = None

class DocumentIndexRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(..., min_length=1)

    @field_validator("file_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Пътят до файла не може да е празен.")
        return value

class TrainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset: str = Field("./dataset", min_length=1)
    output: str = Field("./my_irm_model", min_length=1)
    epochs: int = Field(3, ge=1)
    batch: int = Field(2, ge=1)
    lr: float = Field(2e-4, gt=0)
    lora_r: int = Field(16, ge=1)
    report_to: str = Field("none", min_length=1)

class ClientRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    tolerance: float = Field(1.0, gt=0)
    preferred_method: str = Field("CIE2000")
    preferred_illuminant: str = Field("D65")
    notes: Optional[str] = Field("")

class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: str
    sources: List[str] = Field(default_factory=list)
    timestamp: float
    model: str
