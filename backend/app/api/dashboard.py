from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.inspection import Inspection
from app.models.violation import Violation

router = APIRouter()


@router.get("/dashboard")
def dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(Inspection).count()
    compliant = db.query(Inspection).filter(Inspection.status == "COMPLIANT").count()
    non_compliant = db.query(Inspection).filter(Inspection.status == "NON_COMPLIANT").count()

    common_violations = (
        db.query(Violation.field_name, func.count(Violation.id).label("count"))
        .group_by(Violation.field_name)
        .order_by(func.count(Violation.id).desc())
        .limit(5)
        .all()
    )

    high_severity = db.query(Violation).filter(Violation.severity == "HIGH").count()

    return {
        "total_inspections": total,
        "compliant_inspections": compliant,
        "non_compliant_inspections": non_compliant,
        "common_violations": [{"field_name": f, "count": c} for f, c in common_violations],
        "high_severity_violations": high_severity,
    }
