"""
backend/app/main.py
FastAPI Application Entry Point for NL-SQL Analytics Copilot.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.api import api_router
from backend.app.database.introspection import get_introspection_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nl_to_sql.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.project_name} v{settings.version}...")
    logger.info(f"Target SQLite Database: {settings.db_path}")
    logger.info(f"Live Gemini LLM Available: {settings.is_live_llm_ready} (Model: {settings.gemini_model})")

    # Pre-warm schema introspection cache
    try:
        engine = get_introspection_engine()
        catalog = engine.get_catalog()
        logger.info(f"Introspected {catalog.total_tables} tables, {catalog.total_rows:,} records in {catalog.database_name}")
    except Exception as e:
        logger.warning(f"Initial schema introspection deferred: {e}")

    yield

    logger.info("Shutting down NL-SQL Analytics Copilot...")


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Enterprise AI Copilot converting Natural Language to performant SQLite analytics queries.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api
app.include_router(api_router, prefix="/api")


@app.get("/")
def root_status():
    """Root status endpoint."""
    return {
        "name": settings.project_name,
        "version": settings.version,
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "schema": "/api/schema",
            "chat": "/api/chat",
            "query": "/api/query",
            "execute": "/api/execute",
            "insights": "/api/insights",
            "benchmarks": "/api/benchmarks",
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return structured JSON."""
    logger.error(f"Unhandled server exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "error_type": "internal_server_error",
            "path": request.url.path,
        }
    )
