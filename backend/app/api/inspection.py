import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.database.connection import get_db
from app.models.inspection import Inspection
from app.models.declaration import Declaration
from app.models.violation import Violation
from app.models.rule import Rule
from app.schemas.inspection import InspectionDetail, InspectionListResponse, InspectionListItem
from app.services.ocr_service import extract_declarations
from app.services.compliance_engine import check_compliance
from app.services.evidence_service import build_evidence

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


@router.post("/inspect", response_model=InspectionDetail)
async def inspect_package(image: UploadFile = File(...), db: Session = Depends(get_db)):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported file type '{image.content_type}'.")

    file_bytes = await image.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(413, f"File too large ({size_mb:.1f} MB). Max is {settings.max_upload_mb} MB.")
    if size_mb == 0:
        raise HTTPException(400, "Uploaded file is empty.")

    os.makedirs(settings.upload_dir, exist_ok=True)
    extension = os.path.splitext(image.filename or "")[1] or ".jpg"
    saved_filename = f"{uuid.uuid4()}{extension}"
    saved_path = os.path.join(settings.upload_dir, saved_filename)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # 1. OCR
    ocr_result = extract_declarations(saved_path)
    declarations_raw = ocr_result.get("fields", [])

    # 2. Load active rules
    active_rules = db.query(Rule).filter(Rule.active == True).all()  # noqa: E712

    # 3. Run compliance engine
    result = check_compliance(declarations_raw, active_rules)

    # 4. Persist inspection
    product_name_decl = next((d["value"] for d in declarations_raw if d["name"] == "common_name"), None)
    inspection = Inspection(
        product_name=product_name_decl,
        image_path=saved_path,
        score=result["score"],
        status=result["status"],
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    # 5. Persist declarations, track ids for evidence linking
    declaration_id_map = {}
    for d in declarations_raw:
        row = Declaration(
            inspection_id=inspection.id,
            field_name=d["name"],
            detected_value=d.get("value"),
            confidence=d.get("confidence", 0),
            bounding_box=d.get("bounding_box"),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        declaration_id_map[d["name"]] = row.id

    # 6. Persist violations
    rule_by_field = {r.field_name: r for r in active_rules}
    for v in result["violations"]:
        matched_rule = rule_by_field.get(v["field_name"])
        db.add(Violation(
            inspection_id=inspection.id,
            rule_id=matched_rule.id if matched_rule else None,
            field_name=v["field_name"],
            detected_value=v["detected_value"],
            expected_value=v["expected_value"],
            severity=v["severity"],
            reason=v["reason"],
            confidence=v["confidence"],
            rule_reference=v["rule_reference"],
        ))
    db.commit()

    # 7. Evidence
    build_evidence(db, inspection.id, declarations_raw, declaration_id_map, saved_path)

    db.refresh(inspection)
    return inspection


@router.get("/inspection/{inspection_id}", response_model=InspectionDetail)
def get_inspection(inspection_id: int, db: Session = Depends(get_db)):
    inspection = (
        db.query(Inspection)
        .options(joinedload(Inspection.declarations), joinedload(Inspection.violations))
        .filter(Inspection.id == inspection_id)
        .first()
    )
    if not inspection:
        raise HTTPException(404, "Inspection not found")
    return inspection


@router.get("/inspections", response_model=InspectionListResponse)
def list_inspections(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    query = db.query(Inspection)
    if status_filter:
        query = query.filter(Inspection.status == status_filter)

    total = query.count()
    items = (
        query.order_by(Inspection.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return InspectionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[InspectionListItem.model_validate(i) for i in items],
    )
