"""
backend/app/engine/executor.py
Safe SQLite Query Executor with Latency Measurement and Memory Bounds.
"""

from __future__ import annotations

import time
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from backend.app.config import settings
from backend.app.database.connection import get_readonly_connection


@dataclass
class ExecutionResult:
    """Encapsulates output of executed SQLite query."""
    success: bool
    sql: str
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    error_type: Optional[str] = None


class SQLExecutor:
    """Executes validated read-only SQL queries against SQLite."""

    def __init__(self, db_path: Optional[Path] = None, timeout_sec: Optional[float] = None):
        self.db_path = db_path or settings.db_path
        self.timeout_sec = timeout_sec or settings.query_timeout_seconds

    def execute(self, sql: str) -> ExecutionResult:
        """
        Execute SQL query, measure execution time in milliseconds, and capture row dicts.
        """
        start_time = time.perf_counter()
        target_path = Path(self.db_path).resolve()

        if not target_path.exists():
            target_path = settings.refresh_db_path()
            self.db_path = target_path

        try:
            with get_readonly_connection(target_path, timeout=self.timeout_sec) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                raw_rows = cursor.fetchall()
                
                col_names = [desc[0] for desc in cursor.description] if cursor.description else []
                
                rows_data = []
                for r in raw_rows:
                    row_dict = {}
                    for col in col_names:
                        val = r[col]
                        # Clean special float representations if needed
                        row_dict[col] = val
                    rows_data.append(row_dict)

                exec_time = (time.perf_counter() - start_time) * 1000.0

                return ExecutionResult(
                    success=True,
                    sql=sql,
                    columns=col_names,
                    rows=rows_data,
                    row_count=len(rows_data),
                    execution_time_ms=round(exec_time, 2),
                    error=None,
                    error_type=None,
                )

        except sqlite3.OperationalError as e:
            exec_time = (time.perf_counter() - start_time) * 1000.0
            err_msg = str(e)
            return ExecutionResult(
                success=False,
                sql=sql,
                execution_time_ms=round(exec_time, 2),
                error=err_msg,
                error_type="operational_error" if "no such" in err_msg else "syntax_error",
            )
        except sqlite3.DatabaseError as e:
            exec_time = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                success=False,
                sql=sql,
                execution_time_ms=round(exec_time, 2),
                error=str(e),
                error_type="database_error",
            )
        except Exception as e:
            exec_time = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                success=False,
                sql=sql,
                execution_time_ms=round(exec_time, 2),
                error=str(e),
                error_type="system_error",
            )
