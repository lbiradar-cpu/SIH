from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class Declaration(Base):
    __tablename__ = "declarations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    field_name = Column(String, nullable=False)
    detected_value = Column(String, nullable=True)
    confidence = Column(Float, default=0)
    bounding_box = Column(JSON, nullable=True)  # [x1, y1, x2, y2]

    inspection = relationship("Inspection", back_populates="declarations")
