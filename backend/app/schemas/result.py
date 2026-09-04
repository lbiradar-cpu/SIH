from typing import Optional, List
from pydantic import BaseModel


class ViolationOut(BaseModel):
    field_name: str
    detected_value: Optional[str] = None
    expected_value: Optional[str] = None
    severity: str
    reason: str
    confidence: float = 0
    rule_reference: Optional[str] = None

    class Config:
        from_attributes = True


class ComplianceResult(BaseModel):
    status: str  # COMPLIANT | NON_COMPLIANT
    score: float
    violations: List[ViolationOut] = []
