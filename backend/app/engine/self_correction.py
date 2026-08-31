"""
backend/app/engine/self_correction.py
Agentic NL-to-SQL Pipeline Coordinator with Multi-Turn Self-Correction Loop.
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from backend.app.config import settings
from backend.app.database.introspection import get_introspection_engine
from backend.app.engine.schema_linker import SchemaLinker
from backend.app.engine.validator import SQLValidator, SecurityValidationError
from backend.app.engine.executor import SQLExecutor, ExecutionResult
from backend.app.engine.insights import InsightEngine
from backend.app.engine.provider import get_llm_provider, BaseLLMProvider
from backend.app.models.schemas import ChatResponse, Diagnostics, ExecutiveSummary, ChartSpec


class SelfCorrectionEngine:
    """Coordinates Schema Linking -> SQL Gen -> AST Safety -> SQLite Exec -> Self-Correction Loop."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        provider: Optional[BaseLLMProvider] = None,
        max_retries: int = 3,
    ):
        self.db_path = db_path or settings.db_path
        self.provider = provider or get_llm_provider()
        self.max_retries = max_retries
        self.validator = SQLValidator(max_limit=settings.max_query_rows)
        self.executor = SQLExecutor(db_path=self.db_path, timeout_sec=settings.query_timeout_seconds)

    def process_query(
        self,
        question: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        offline_mode: bool = False,
        temperature: float = 0.0,
    ) -> ChatResponse:
        """
        Execute full NL-to-SQL pipeline with error-intercepting iterative repair loop.
        """
        overall_start = time.perf_counter()
        timings: Dict[str, float] = {}
        trace: List[Dict[str, Any]] = []

        # Use specific provider if offline_mode requested
        active_provider = get_llm_provider(force_offline=offline_mode) if offline_mode else self.provider

        # Stage 1: Schema Linking
        t0 = time.perf_counter()
        linker = SchemaLinker()
        linked_tables, schema_context = linker.link_schema(question)
        timings["schema_linking_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

        # Stage 2: Initial SQL Generation
        t1 = time.perf_counter()
        current_sql = active_provider.generate_sql(
            question=question,
            schema_context=schema_context,
            dialect="sqlite",
            conversation_history=conversation_history,
        )
        timings["sql_generation_ms"] = round((time.perf_counter() - t1) * 1000.0, 2)

        sanitized_sql = current_sql
        exec_result: Optional[ExecutionResult] = None
        attempts = 0

        # Stages 3-6: Iterative Validation & Execution Loop (Up to max_retries)
        while attempts <= self.max_retries:
            attempts += 1
            attempt_record: Dict[str, Any] = {
                "attempt": attempts,
                "sql": current_sql,
                "status": "pending",
                "error": None,
            }

            # 3. Security & AST Validation
            t_val = time.perf_counter()
            try:
                sanitized_sql = self.validator.validate_and_sanitize(current_sql, enforce_limit=True)
                timings["ast_validation_ms"] = round((time.perf_counter() - t_val) * 1000.0, 2)
            except SecurityValidationError as sec_err:
                attempt_record["status"] = "security_violation"
                attempt_record["error"] = str(sec_err)
                trace.append(attempt_record)
                total_latency = round((time.perf_counter() - overall_start) * 1000.0, 2)
                timings["total_latency_ms"] = total_latency

                return ChatResponse(
                    success=False,
                    question=question,
                    session_id=session_id,
                    sql=current_sql,
                    columns=[],
                    rows=[],
                    row_count=0,
                    execution_time_ms=0.0,
                    pipeline_timings=timings,
                    explanation=f"Query rejected by security guardrail: {sec_err}",
                    diagnostics=Diagnostics(
                        attempts=attempts,
                        is_live_ai=active_provider.is_live_ai,
                        model_used=active_provider.provider_name,
                        tables_linked=linked_tables,
                        trace=trace,
                    ),
                    correction_attempts=attempts - 1,
                    correction_log=trace,
                    error=str(sec_err),
                    error_type="security_violation",
                )

            # 4. Safe SQLite Execution
            t_exec = time.perf_counter()
            exec_result = self.executor.execute(sanitized_sql)
            timings["db_execution_ms"] = exec_result.execution_time_ms

            if exec_result.success:
                attempt_record["status"] = "success"
                trace.append(attempt_record)
                break
            else:
                # Intercept runtime execution error
                attempt_record["status"] = "execution_error"
                attempt_record["error"] = exec_result.error
                trace.append(attempt_record)

                if attempts <= self.max_retries:
                    # Trigger repair attempt
                    current_sql = active_provider.repair_sql(
                        question=question,
                        failed_sql=sanitized_sql,
                        error_message=exec_result.error or "Execution error",
                        schema_context=schema_context,
                    )
                else:
                    break

        total_latency = round((time.perf_counter() - overall_start) * 1000.0, 2)
        timings["total_latency_ms"] = total_latency

        # Check if final execution succeeded
        if exec_result and exec_result.success:
            # Stage 7: Executive Summary & Visualizer Spec Generation
            t_ins = time.perf_counter()
            exec_summary = InsightEngine.generate_executive_summary(
                question=question,
                columns=exec_result.columns,
                rows=exec_result.rows,
                sql=sanitized_sql,
            )
            chart_spec = InsightEngine.generate_chart_spec(
                question=question,
                columns=exec_result.columns,
                rows=exec_result.rows,
                sql=sanitized_sql,
            )
            followups = InsightEngine.generate_followups(
                question=question,
                columns=exec_result.columns,
                rows=exec_result.rows,
            )
            timings["insight_synthesis_ms"] = round((time.perf_counter() - t_ins) * 1000.0, 2)

            explanation = (
                f"Generated SQLite query linking [{', '.join(linked_tables)}] to answer: '{question}'. "
                f"Executed in {exec_result.execution_time_ms:.1f}ms returning {exec_result.row_count} rows."
            )

            return ChatResponse(
                success=True,
                question=question,
                session_id=session_id,
                sql=sanitized_sql,
                columns=exec_result.columns,
                rows=exec_result.rows,
                row_count=exec_result.row_count,
                execution_time_ms=exec_result.execution_time_ms,
                pipeline_timings=timings,
                explanation=explanation,
                executive_summary=exec_summary,
                chart_spec=chart_spec,
                suggested_followups=followups,
                diagnostics=Diagnostics(
                    attempts=attempts,
                    is_live_ai=active_provider.is_live_ai,
                    model_used=active_provider.provider_name,
                    tables_linked=linked_tables,
                    trace=trace,
                ),
                correction_attempts=attempts - 1,
                correction_log=trace,
                error=None,
                error_type=None,
            )
        else:
            err_msg = exec_result.error if exec_result else "Execution failed after retries."
            err_type = exec_result.error_type if exec_result else "execution_error"

            return ChatResponse(
                success=False,
                question=question,
                session_id=session_id,
                sql=sanitized_sql,
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=exec_result.execution_time_ms if exec_result else 0.0,
                pipeline_timings=timings,
                explanation=f"Query failed after {attempts} attempts: {err_msg}",
                diagnostics=Diagnostics(
                    attempts=attempts,
                    is_live_ai=active_provider.is_live_ai,
                    model_used=active_provider.provider_name,
                    tables_linked=linked_tables,
                    trace=trace,
                ),
                correction_attempts=attempts - 1,
                correction_log=trace,
                error=err_msg,
                error_type=err_type,
            )
