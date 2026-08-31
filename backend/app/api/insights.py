"""
backend/app/api/insights.py
Executive Business Insights and Chart Advisor Endpoints.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.engine.insights import InsightEngine
from backend.app.models.schemas import ExecutiveSummary, ChartSpec

router = APIRouter()


class InsightsRequest(BaseModel):
    """Payload for on-demand insight and chart generation."""
    question: str
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    sql: Optional[str] = None


class InsightsResponse(BaseModel):
    """On-demand insight and chart synthesis response."""
    executive_summary: ExecutiveSummary
    chart_spec: ChartSpec
    suggested_followups: List[str] = Field(default_factory=list)


@router.post("/insights", response_model=InsightsResponse)
def generate_insights(req: InsightsRequest) -> InsightsResponse:
    """Generate executive narrative summary, KPI highlights, and chart specifications."""
    exec_summary = InsightEngine.generate_executive_summary(
        question=req.question,
        columns=req.columns,
        rows=req.rows,
        sql=req.sql or "",
    )
    chart_spec = InsightEngine.generate_chart_spec(
        question=req.question,
        columns=req.columns,
        rows=req.rows,
        sql=req.sql or "",
    )
    followups = InsightEngine.generate_followups(
        question=req.question,
        columns=req.columns,
        rows=req.rows,
    )

    return InsightsResponse(
        executive_summary=exec_summary,
        chart_spec=chart_spec,
        suggested_followups=followups,
    )
