from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.inspection import Inspection

router = APIRouter()


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    """Distinct products seen across inspections, with inspection counts."""
    rows = (
        db.query(Inspection.product_name, func.count(Inspection.id))
        .filter(Inspection.product_name.isnot(None))
        .group_by(Inspection.product_name)
        .all()
    )
    return [{"product_name": name, "inspection_count": count} for name, count in rows]
