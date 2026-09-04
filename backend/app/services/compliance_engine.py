"""
services/compliance_engine.py

Receives structured declarations (from OCR) + active rules (from DB),
checks presence/format, generates violations with rule references, and
returns a structured compliance result. Contains NO route/HTTP logic and
NO hardcoded legal text - rules are passed in as data.

IMPORTANT LIMITATION: this only checks what is machine-checkable
(presence of a field, basic format of a value). It does NOT determine
legal compliance on its own - results are meant to be reviewed by a
human enforcement official. Each violation keeps detected value,
confidence, and rule reference separate so that review is possible.
"""

import re

from app.services.scoring_service import calculate_score

CONFIDENCE_THRESHOLD = 0.6


def _field_present(declarations_by_name: dict, field_name: str) -> bool:
    decl = declarations_by_name.get(field_name)
    return decl is not None and decl.get("value") not in (None, "", "N/A")


def _format_valid(field_name: str, value: str) -> bool:
    if field_name == "net_quantity":
        return bool(re.search(r"\d+(\.\d+)?\s*(g|kg|ml|l|mg|pcs|n)\b", value, re.IGNORECASE))
    if field_name == "mrp":
        return bool(re.search(r"\d+(\.\d+)?", value))
    return True  # no specific format check for this field yet


def check_compliance(declarations: list, rules: list) -> dict:
    """
    declarations: list of dicts like {"name": ..., "value": ..., "confidence": ..., "bounding_box": ...}
    rules: list of Rule model instances (active rules only)
    """
    declarations_by_name = {d["name"]: d for d in declarations}
    violations = []

    for rule in rules:
        field = rule.field_name

        if not _field_present(declarations_by_name, field):
            violations.append({
                "field_name": field,
                "detected_value": None,
                "expected_value": rule.description,
                "severity": "HIGH",
                "reason": "Required declaration not detected",
                "confidence": 0.0,
                "rule_reference": rule.source_reference,
            })
            continue

        decl = declarations_by_name[field]

        # Low OCR confidence -> flag for human review, don't assume violation
        if decl["confidence"] < CONFIDENCE_THRESHOLD:
            violations.append({
                "field_name": field,
                "detected_value": decl["value"],
                "expected_value": rule.description,
                "severity": "MEDIUM",
                "reason": "Detected but with low confidence - requires manual review",
                "confidence": decl["confidence"],
                "rule_reference": rule.source_reference,
            })
            continue

        if rule.requirement == "required_present_with_unit" and not _format_valid(field, decl["value"]):
            violations.append({
                "field_name": field,
                "detected_value": decl["value"],
                "expected_value": "Value with a valid unit (e.g. 500 g, 1 l)",
                "severity": "MEDIUM",
                "reason": "Detected value does not match expected format",
                "confidence": decl["confidence"],
                "rule_reference": rule.source_reference,
            })

    score = calculate_score(total_rules=len(rules), violations=violations)
    status = "COMPLIANT" if score == 100 else "NON_COMPLIANT"

    return {"status": status, "score": score, "violations": violations}
