from pydantic import BaseModel, Field
from typing import Optional

class ClientCreateRequest(BaseModel):
    name: str = Field(..., example="Client A")
    tolerance: float = Field(..., gt=0, example=1.0)
    preferred_method: str = Field(..., example="CIE76")
