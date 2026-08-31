"""
backend/app/api/__init__.py
API Router Aggregation.
"""

from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.schema import router as schema_router
from backend.app.api.chat import router as chat_router
from backend.app.api.insights import router as insights_router
from backend.app.api.benchmarks import router as benchmarks_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(schema_router, tags=["Schema"])
api_router.include_router(chat_router, tags=["Chat & Query"])
api_router.include_router(insights_router, tags=["Insights"])
api_router.include_router(benchmarks_router, tags=["Benchmarks"])
