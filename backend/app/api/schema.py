"""
backend/app/api/schema.py
Dynamic Schema Introspection and Catalog Refresh Endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter
from backend.app.database.introspection import get_introspection_engine
from backend.app.models.schemas import SchemaResponse

router = APIRouter()


@router.get("/schema", response_model=SchemaResponse)
def get_database_schema() -> SchemaResponse:
    """Retrieve introspected SQLite database schema, tables, columns, and foreign keys."""
    engine = get_introspection_engine()
    return engine.to_schema_response()


@router.post("/schema/refresh", response_model=SchemaResponse)
def refresh_database_schema() -> SchemaResponse:
    """Force cache invalidation and re-introspect the active SQLite database."""
    engine = get_introspection_engine()
    engine.refresh()
    return engine.to_schema_response()
