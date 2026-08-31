"""
backend/app/api/health.py
System Health and Diagnostics Endpoint.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from fastapi import APIRouter
from pathlib import Path

from backend.app.config import settings
from backend.app.database.connection import get_readonly_connection
from backend.app.database.introspection import get_introspection_engine
from backend.app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health_status() -> HealthResponse:
    """Check backend operational health, database connectivity, and LLM readiness."""
    db_connected = False
    total_orders = 0
    target_path = Path(settings.db_path).resolve()

    if target_path.exists():
        try:
            with get_readonly_connection(target_path, timeout=2.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                db_connected = True
                try:
                    cursor.execute("SELECT COUNT(*) FROM orders;")
                    total_orders = cursor.fetchone()[0]
                except Exception:
                    # Database may not have orders table (e.g. Chinook)
                    total_orders = 0
        except Exception:
            db_connected = False

    llm_provider = settings.gemini_model if settings.is_live_llm_ready else "DeterministicFallbackEngine"
    llm_available = settings.is_live_llm_ready

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        version=settings.version,
        database_connected=db_connected,
        database_file=target_path.name,
        total_orders=total_orders,
        llm_provider=llm_provider,
        llm_available=llm_available,
        offline_mode_ready=True,
        timestamp=now_iso,
    )
