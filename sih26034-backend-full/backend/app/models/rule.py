from sqlalchemy import Column, Integer, String, Boolean

from app.database.base import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String, unique=True, nullable=False)
    field_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    requirement = Column(String, nullable=False)  # e.g. required_present, required_present_with_unit
    source_reference = Column(String, nullable=False)
    version = Column(String, nullable=False)
    active = Column(Boolean, default=True)
