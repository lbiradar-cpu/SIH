from typing import Optional, List
from pydantic import BaseModel


class DeclarationOut(BaseModel):
    id: int
    field_name: str
    detected_value: Optional[str] = None
    confidence: float
    bounding_box: Optional[List[float]] = None

    class Config:
        from_attributes = True
