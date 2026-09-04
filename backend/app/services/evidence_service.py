"""
services/evidence_service.py
Builds Evidence rows linking each declaration back to the source image
and its bounding box, so an enforcement official can verify what the
system actually detected.
"""

from sqlalchemy.orm import Session

from app.models.evidence import Evidence


def build_evidence(db: Session, inspection_id: int, declarations: list, declaration_id_map: dict, image_path: str):
    evidence_rows = []
    for decl in declarations:
        evidence_rows.append(Evidence(
            inspection_id=inspection_id,
            declaration_id=declaration_id_map.get(decl["name"]),
            image_path=image_path,
            extracted_text=decl.get("value"),
            bounding_box=decl.get("bounding_box"),
        ))
    db.add_all(evidence_rows)
    db.commit()
    return evidence_rows
