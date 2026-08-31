"""
backend/app/config.py
Configuration and Environment Settings for NL-SQL Analytics Copilot Backend.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

WORKSPACE_ROOT = Path(__file__).parent.parent.parent.resolve()


def resolve_database_path() -> Path:
    """Find the best available SQLite database file."""
    # Priority order:
    # 1. Custom env var SQLITE_DB_PATH or DATABASE_URL
    custom_path = os.getenv("SQLITE_DB_PATH") or os.getenv("DATABASE_PATH")
    if custom_path:
        p = Path(custom_path)
        if p.is_absolute():
            return p
        return WORKSPACE_ROOT / p

    # 2. ecommerce.db in workspace root
    ecommerce_db = WORKSPACE_ROOT / "ecommerce.db"
    if ecommerce_db.exists() and ecommerce_db.stat().st_size > 0:
        return ecommerce_db

    # 3. data/ecommerce.db
    data_ecommerce = WORKSPACE_ROOT / "data" / "ecommerce.db"
    if data_ecommerce.exists() and data_ecommerce.stat().st_size > 0:
        return data_ecommerce

    # 4. chinook.db fallback
    chinook_db = WORKSPACE_ROOT / "chinook.db"
    if chinook_db.exists():
        return chinook_db

    # Default to ecommerce.db in workspace root
    return ecommerce_db


class Settings(BaseModel):
    """Application Settings Model."""
    project_name: str = "NL-SQL Analytics Copilot"
    version: str = "2.0.0"
    api_prefix: str = "/api"
    
    # Host & Port
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Database
    db_path: Path = resolve_database_path()
    query_timeout_seconds: float = float(os.getenv("QUERY_TIMEOUT_SECONDS", "5.0"))
    max_query_rows: int = int(os.getenv("MAX_QUERY_ROWS", "1000"))

    # Gemini LLM Provider
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))

    # Offline Mode Flag
    force_offline_mode: bool = os.getenv("OFFLINE_MODE", "false").lower() in ("true", "1", "yes")

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    @property
    def is_live_llm_ready(self) -> bool:
        """Check if live Gemini LLM credentials are provided."""
        return bool(self.gemini_api_key) and not self.force_offline_mode

    def refresh_db_path(self) -> Path:
        """Re-evaluate database path after dataset generation."""
        self.db_path = resolve_database_path()
        return self.db_path


settings = Settings()
