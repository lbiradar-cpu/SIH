import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.inspection import Inspection
from app.services.report_service import generate_report_pdf

router = APIRouter()


@router.post("/inspection/{inspection_id}/report")
def generate_report(inspection_id: int, db: Session = Depends(get_db)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(404, "Inspection not found")

    path = generate_report_pdf(inspection, inspection.declarations, inspection.violations)
    return {"report_path": path, "download_url": f"/api/inspection/{inspection_id}/report/download"}


@router.get("/inspection/{inspection_id}/report/download")
def download_report(inspection_id: int):
    path = os.path.join("reports", f"inspection_{inspection_id}_report.pdf")
    if not os.path.exists(path):
        raise HTTPException(404, "Report not generated yet. POST to /report first.")
    return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))
