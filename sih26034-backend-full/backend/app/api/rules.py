from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.rule import Rule

router = APIRouter()


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(Rule).filter(Rule.active == True).all()  # noqa: E712
    return [
        {
            "id": r.id,
            "rule_code": r.rule_code,
            "field_name": r.field_name,
            "description": r.description,
            "requirement": r.requirement,
            "source_reference": r.source_reference,
            "version": r.version,
        }
        for r in rules
    ]
