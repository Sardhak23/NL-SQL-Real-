"""
backend/app/models/schemas.py
Pydantic v2 Request & Response Data Contracts for NL-SQL Analytics Copilot.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, model_validator


# ==============================================================================
# Request Models
# ==============================================================================

class ChatRequest(BaseModel):
    """Primary NL-to-SQL query request."""
    question: Optional[str] = None
    prompt: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    dialect: str = "sqlite"
    temperature: float = 0.0
    max_retries: int = 3
    offline_mode: bool = False

    @model_validator(mode="after")
    def unify_question_and_session(self) -> "ChatRequest":
        # Synchronize question and prompt
        if not self.question and self.prompt:
            self.question = self.prompt
        elif not self.prompt and self.question:
            self.prompt = self.question

        # Synchronize session_id and conversation_id
        if not self.session_id and self.conversation_id:
            self.session_id = self.conversation_id
        elif not self.conversation_id and self.session_id:
            self.conversation_id = self.session_id

        if not self.question:
            raise ValueError("Either 'question' or 'prompt' must be provided.")
        return self


class QueryRequest(ChatRequest):
    """Alias for ChatRequest for backwards and REST compatibility."""
    pass


class ExecuteRequest(BaseModel):
    """Direct SQL execution request."""
    sql: Optional[str] = None
    sql_query: Optional[str] = None
    timeout_sec: float = 5.0

    @model_validator(mode="after")
    def unify_sql(self) -> "ExecuteRequest":
        if not self.sql and self.sql_query:
            self.sql = self.sql_query
        elif not self.sql_query and self.sql:
            self.sql_query = self.sql

        if not self.sql:
            raise ValueError("SQL query string is required.")
        return self


# ==============================================================================
# Nested Insight & Visualizer Models
# ==============================================================================

class MetricItem(BaseModel):
    """Scalar KPI metric value card."""
    label: str
    value: Union[str, int, float]
    subtext: Optional[str] = None
    change: Optional[str] = None


class ExecutiveSummary(BaseModel):
    """Executive narrative summary & KPIs."""
    headline: str = ""
    key_metrics: List[MetricItem] = Field(default_factory=list)
    metrics: Optional[List[MetricItem]] = None
    bullet_points: List[str] = Field(default_factory=list)
    takeaways: Optional[List[str]] = None
    actionable_recommendations: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unify_fields(self) -> "ExecutiveSummary":
        if not self.metrics and self.key_metrics:
            self.metrics = self.key_metrics
        elif not self.key_metrics and self.metrics:
            self.key_metrics = self.metrics

        if not self.takeaways and self.bullet_points:
            self.takeaways = self.bullet_points
        elif not self.bullet_points and self.takeaways:
            self.bullet_points = self.takeaways
        return self


class ChartSpec(BaseModel):
    """Recharts & UI Visualization Specification."""
    chart_type: str = "table"
    recommended_chart: Optional[str] = None
    recommended_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    secondary_y_axis: Optional[str] = None
    series: Optional[List[str]] = None
    is_plottable: bool = True
    format: Optional[str] = None
    chart_config: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def unify_chart_names(self) -> "ChartSpec":
        c_type = self.chart_type or self.recommended_chart or self.recommended_type or "table"
        self.chart_type = c_type
        self.recommended_chart = c_type
        self.recommended_type = c_type
        return self


class Diagnostics(BaseModel):
    """Pipeline diagnostics and self-correction telemetry."""
    attempts: int = 1
    is_live_ai: bool = False
    model_used: str = "DeterministicFallbackEngine"
    tables_linked: List[str] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)


# ==============================================================================
# Primary Response Models
# ==============================================================================

class ChatResponse(BaseModel):
    """Unified API response for NL-to-SQL generation and execution."""
    success: bool = True
    question: str = ""
    prompt: Optional[str] = None
    session_id: Optional[str] = None
    sql: str = ""
    sql_query: Optional[str] = None
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    data: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    execution_time_ms: float = 0.0
    pipeline_timings: Dict[str, float] = Field(default_factory=dict)
    explanation: Optional[str] = None
    sql_explanation: Optional[List[str]] = None
    executive_summary: Optional[ExecutiveSummary] = None
    chart_spec: Optional[ChartSpec] = None
    visualization: Optional[Dict[str, Any]] = None
    diagnostics: Optional[Diagnostics] = None
    suggested_followups: List[str] = Field(default_factory=list)
    correction_attempts: int = 0
    correction_log: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    error_type: Optional[str] = None

    @model_validator(mode="after")
    def sync_aliases(self) -> "ChatResponse":
        # Question / Prompt
        if not self.prompt and self.question:
            self.prompt = self.question
        elif not self.question and self.prompt:
            self.question = self.prompt

        # SQL / SQL Query
        if not self.sql_query and self.sql:
            self.sql_query = self.sql
        elif not self.sql and self.sql_query:
            self.sql = self.sql_query

        # Rows / Data
        if self.data is None:
            self.data = self.rows
        elif not self.rows and self.data:
            self.rows = self.data

        # Row count
        if self.row_count == 0 and self.rows:
            self.row_count = len(self.rows)

        # Visualization mapping
        if self.chart_spec and not self.visualization:
            self.visualization = {
                "recommended_chart": self.chart_spec.chart_type,
                "supported_charts": [self.chart_spec.chart_type, "table"],
                "chart_config": {
                    "x_axis": self.chart_spec.x_axis,
                    "y_axis": self.chart_spec.y_axis,
                    "title": self.chart_spec.title,
                    "format": self.chart_spec.format or "standard",
                }
            }
        return self


class QueryResponse(ChatResponse):
    """Alias for QueryResponse."""
    pass


# ==============================================================================
# Database Schema Introspection Models
# ==============================================================================

class ColumnInfo(BaseModel):
    """Column metadata definition."""
    name: str
    type: str
    is_pk: bool = False
    is_fk: bool = False
    nullable: bool = True
    sample_values: List[Any] = Field(default_factory=list)


class ForeignKeyInfo(BaseModel):
    """Foreign key relation metadata."""
    column: str
    referenced_table: str
    referenced_column: str


class TableInfo(BaseModel):
    """Table schema metadata."""
    name: str
    row_count: int = 0
    description: Optional[str] = None
    columns: List[ColumnInfo] = Field(default_factory=list)
    foreign_keys: List[ForeignKeyInfo] = Field(default_factory=list)


class SchemaResponse(BaseModel):
    """Database schema catalog response."""
    database_name: str
    dialect: str = "sqlite"
    total_tables: int
    total_rows: int
    tables: List[TableInfo] = Field(default_factory=list)


# ==============================================================================
# System Health Models
# ==============================================================================

class HealthResponse(BaseModel):
    """System health check & engine status."""
    status: str = "healthy"
    version: str = "2.0.0"
    database_connected: bool = True
    database_file: str = "ecommerce.db"
    total_orders: int = 0
    llm_provider: str = "DeterministicFallbackEngine"
    llm_available: bool = False
    offline_mode_ready: bool = True
    timestamp: str = ""
