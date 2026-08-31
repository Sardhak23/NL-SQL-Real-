"""
backend/app/database/connection.py
SQLite Connection Factory and Context Managers with Read-Only Safety and PRAGMA Optimization.
"""

from __future__ import annotations

import sqlite3
import contextlib
from pathlib import Path
from typing import Generator, Optional
from backend.app.config import settings


@contextlib.contextmanager
def get_connection(
    db_path: Optional[Path] = None,
    readonly: bool = True,
    timeout: Optional[float] = None
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager yielding a thread-safe SQLite connection.
    In read-only mode, enforces SQLite ?mode=ro URI and PRAGMA query_only = ON.
    """
    target_path = Path(db_path or settings.db_path).resolve()
    timeout_sec = timeout if timeout is not None else settings.query_timeout_seconds

    if not target_path.exists():
        # Fallback to refresh settings
        target_path = settings.refresh_db_path()

    if readonly:
        # Connect in read-only URI mode
        uri_path = f"file:{target_path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True, timeout=timeout_sec, check_same_thread=False)
        try:
            conn.execute("PRAGMA query_only = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            conn.close()
    else:
        # Read-write connection (used for setup or schema creation)
        conn = sqlite3.connect(str(target_path), timeout=timeout_sec, check_same_thread=False)
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            conn.close()


@contextlib.contextmanager
def get_readonly_connection(
    db_path: Optional[Path] = None,
    timeout: Optional[float] = None
) -> Generator[sqlite3.Connection, None, None]:
    """Convenience shortcut for read-only analytical connections."""
    with get_connection(db_path=db_path, readonly=True, timeout=timeout) as conn:
        yield conn
