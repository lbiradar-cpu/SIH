"""
api/health.py

One job: let anyone (frontend, teammates, deployment platform) check
"is the backend alive?" without needing auth or touching the database.

This is the first thing you test when something feels broken -
if /api/health fails, the problem is your server, not your logic.
"""

from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
def health_check():
    """
    GET /api/health

    Purpose: Confirm the backend process is running and responding.

    Request: none (no body, no params)

    Response 200:
    {
        "status": "ok",
        "service": "legal-metrology-backend",
        "timestamp": "2026-09-04T10:00:00Z"
    }
    """
    return {
        "status": "ok",
        "service": "legal-metrology-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
