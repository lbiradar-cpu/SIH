from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.base import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_name = Column(String, nullable=True)
    image_path = Column(String, nullable=False)
    score = Column(Float, default=0)
    status = Column(String, default="PENDING")  # PENDING | COMPLIANT | NON_COMPLIANT
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="inspections")
    declarations = relationship("Declaration", back_populates="inspection", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="inspection", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="inspection", cascade="all, delete-orphan")
