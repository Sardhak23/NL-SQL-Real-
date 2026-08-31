"""
backend/app/api/chat.py
Conversational NL-to-SQL, Direct Execution, and Self-Correction Endpoints.
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional
from fastapi import APIRouter

from backend.app.config import settings
from backend.app.engine.self_correction import SelfCorrectionEngine
from backend.app.engine.validator import SQLValidator, SecurityValidationError
from backend.app.engine.executor import SQLExecutor
from backend.app.engine.insights import InsightEngine
from backend.app.models.schemas import (
    ChatRequest,
    ChatResponse,
    QueryRequest,
    QueryResponse,
    ExecuteRequest,
    Diagnostics,
)

router = APIRouter()

# In-memory session history storage
_SESSION_HISTORY: Dict[str, List[Dict[str, Any]]] = {}


@router.post("/chat", response_model=ChatResponse)
def handle_chat_query(req: ChatRequest) -> ChatResponse:
    """
    Process natural language business inquiry through the Agentic NL-to-SQL pipeline.
    Executes schema linking, SQL generation, AST safety validation, SQLite execution,
    multi-turn self-correction, executive narrative synthesis, and Recharts spec generation.
    """
    session_id = req.session_id or "default_session"
    history = _SESSION_HISTORY.get(session_id, [])

    engine = SelfCorrectionEngine(
        max_retries=req.max_retries,
    )

    response = engine.process_query(
        question=req.question or req.prompt or "",
        session_id=session_id,
        conversation_history=history,
        offline_mode=req.offline_mode or settings.force_offline_mode,
        temperature=req.temperature,
    )

    # Record turn in session history if successful
    if response.success and response.sql:
        turn_record = {
            "question": response.question,
            "sql": response.sql,
            "row_count": response.row_count,
            "headline": response.executive_summary.headline if response.executive_summary else "",
        }
        if session_id not in _SESSION_HISTORY:
            _SESSION_HISTORY[session_id] = []
        _SESSION_HISTORY[session_id].append(turn_record)

    return response


@router.post("/query", response_model=ChatResponse)
def handle_query_alias(req: QueryRequest) -> ChatResponse:
    """Alias for POST /api/chat."""
    return handle_chat_query(req)


@router.post("/execute", response_model=ChatResponse)
def handle_direct_execute(req: ExecuteRequest) -> ChatResponse:
    """
    Directly execute user-provided or edited SQL with read-only safety guardrails.
    """
    raw_sql = req.sql or req.sql_query or ""
    validator = SQLValidator(max_limit=settings.max_query_rows)
    executor = SQLExecutor(timeout_sec=req.timeout_sec)

    start_time = time.perf_counter()

    # Safety validation
    try:
        sanitized_sql = validator.validate_and_sanitize(raw_sql, enforce_limit=True)
    except SecurityValidationError as sec_err:
        return ChatResponse(
            success=False,
            question="Direct SQL Execution",
            sql=raw_sql,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=0.0,
            explanation=f"Query rejected by security guardrail: {sec_err}",
            diagnostics=Diagnostics(
                attempts=1,
                is_live_ai=False,
                model_used="ManualSQLEditor",
                trace=[{"attempt": 1, "sql": raw_sql, "status": "security_violation", "error": str(sec_err)}],
            ),
            error=str(sec_err),
            error_type="security_violation",
        )

    # Safe execution
    exec_result = executor.execute(sanitized_sql)
    total_time = round((time.perf_counter() - start_time) * 1000.0, 2)

    if exec_result.success:
        exec_summary = InsightEngine.generate_executive_summary(
            question="Direct SQL Query Result",
            columns=exec_result.columns,
            rows=exec_result.rows,
            sql=sanitized_sql,
        )
        chart_spec = InsightEngine.generate_chart_spec(
            question="Direct SQL Query",
            columns=exec_result.columns,
            rows=exec_result.rows,
            sql=sanitized_sql,
        )
        followups = InsightEngine.generate_followups(
            question="Direct SQL Query",
            columns=exec_result.columns,
            rows=exec_result.rows,
        )

        return ChatResponse(
            success=True,
            question="Direct SQL Query",
            sql=sanitized_sql,
            columns=exec_result.columns,
            rows=exec_result.rows,
            row_count=exec_result.row_count,
            execution_time_ms=exec_result.execution_time_ms,
            pipeline_timings={"db_execution_ms": exec_result.execution_time_ms, "total_latency_ms": total_time},
            explanation=f"Executed manual SQL query returning {exec_result.row_count} rows in {exec_result.execution_time_ms}ms.",
            executive_summary=exec_summary,
            chart_spec=chart_spec,
            suggested_followups=followups,
            diagnostics=Diagnostics(
                attempts=1,
                is_live_ai=False,
                model_used="ManualSQLEditor",
                trace=[{"attempt": 1, "sql": sanitized_sql, "status": "success", "error": None}],
            ),
            error=None,
            error_type=None,
        )
    else:
        return ChatResponse(
            success=False,
            question="Direct SQL Query",
            sql=sanitized_sql,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=exec_result.execution_time_ms,
            pipeline_timings={"db_execution_ms": exec_result.execution_time_ms, "total_latency_ms": total_time},
            explanation=f"Execution error: {exec_result.error}",
            diagnostics=Diagnostics(
                attempts=1,
                is_live_ai=False,
                model_used="ManualSQLEditor",
                trace=[{"attempt": 1, "sql": sanitized_sql, "status": "execution_error", "error": exec_result.error}],
            ),
            error=exec_result.error,
            error_type=exec_result.error_type or "execution_error",
        )
