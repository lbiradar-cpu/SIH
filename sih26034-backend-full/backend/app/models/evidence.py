from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    declaration_id = Column(Integer, ForeignKey("declarations.id"), nullable=True)
    image_path = Column(String, nullable=False)
    extracted_text = Column(String, nullable=True)
    bounding_box = Column(JSON, nullable=True)

    inspection = relationship("Inspection", back_populates="evidence")
