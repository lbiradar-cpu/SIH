from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=True)
    field_name = Column(String, nullable=False)
    detected_value = Column(String, nullable=True)
    expected_value = Column(String, nullable=True)
    severity = Column(String, nullable=False)  # HIGH | MEDIUM | LOW
    reason = Column(String, nullable=False)
    confidence = Column(Float, default=0)
    rule_reference = Column(String, nullable=True)

    inspection = relationship("Inspection", back_populates="violations")
