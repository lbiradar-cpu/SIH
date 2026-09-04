from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.schemas.declaration import DeclarationOut
from app.schemas.result import ViolationOut


class InspectionListItem(BaseModel):
    id: int
    product_name: Optional[str] = None
    score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InspectionDetail(BaseModel):
    id: int
    product_name: Optional[str] = None
    image_path: str
    score: float
    status: str
    created_at: datetime
    declarations: List[DeclarationOut] = []
    violations: List[ViolationOut] = []

    class Config:
        from_attributes = True


class InspectionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[InspectionListItem]
