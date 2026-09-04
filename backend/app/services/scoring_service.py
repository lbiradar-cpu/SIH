"""
services/scoring_service.py
Pure function: given the number of active rules and the violations found,
compute a 0-100 compliance score. Kept separate from compliance_engine.py
so scoring logic can change without touching rule-evaluation logic.
"""

SEVERITY_WEIGHTS = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def calculate_score(total_rules: int, violations: list) -> float:
    if total_rules == 0:
        return 100.0

    max_penalty = total_rules * SEVERITY_WEIGHTS["HIGH"]
    penalty = sum(SEVERITY_WEIGHTS.get(v["severity"], 1) for v in violations)

    score = 100 * (1 - (penalty / max_penalty))
    return round(max(score, 0), 2)
