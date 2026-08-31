"""
tests/test_chart_heuristics.py
Unit tests for Automated Chart Advisor & Visualizer Heuristics.
"""
import pytest
from typing import Dict, List, Any


def determine_chart_archetype(
    col_names: List[str],
    col_types: Dict[str, str],
    row_count: int,
    distinct_counts: Dict[str, int] = None,
) -> str:
    """
    Standard deterministic heuristic classifier for chart type selection.
    """
    distinct_counts = distinct_counts or {}

    # Rule 1: Single cell (1 row, 1 numeric col) -> Metric Card
    if row_count == 1:
        num_cols = [c for c in col_names if col_types.get(c) in ("numeric", "int", "float", "real")]
        if len(num_cols) >= 1:
            return "metric"

    # Rule 2: Temporal column present + numeric metric -> Line or Area Chart
    time_cols = [
        c
        for c in col_names
        if col_types.get(c) in ("date", "time", "datetime", "timestamp")
        or any(k in c.lower() for k in ("month", "year", "date", "day", "quarter", "hour"))
    ]
    num_cols = [
        c
        for c in col_names
        if col_types.get(c) in ("numeric", "int", "float", "real", "decimal")
        or any(
            k in c.lower()
            for k in (
                "revenue",
                "sales",
                "amount",
                "spend",
                "price",
                "count",
                "orders",
                "total",
                "avg",
                "sum",
                "rate",
                "pct",
            )
        )
    ]

    if time_cols and num_cols:
        # If cumulative or daily timeline -> area or line
        if any("cumul" in c.lower() for c in col_names):
            return "area"
        return "line"

    # Rule 3: Single Categorical + Single Numeric
    cat_cols = [c for c in col_names if c not in time_cols and c not in num_cols]
    if len(cat_cols) == 1 and len(num_cols) >= 1:
        cat_name = cat_cols[0]
        distinct_cnt = distinct_counts.get(cat_name, row_count)

        # Low cardinality share (2-6 distinct categories) -> Donut Chart
        if distinct_cnt <= 6 and any(k in cat_name.lower() for k in ("status", "method", "tier", "segment")):
            return "donut"

        # Ranking (7-30 categories) -> Bar Chart
        if distinct_cnt <= 30:
            return "bar"

    # Rule 4: 2 Numeric Metrics + entity col (Correlation) -> Scatter
    if len(num_cols) >= 2 and len(col_names) <= 3 and row_count >= 10:
        if any("corr" in c.lower() for c in col_names):
            return "scatter"

    # Rule 5: High dimensional / multi-attribute -> Table
    return "table"


def test_metric_card_heuristics():
    """Verify single aggregate values produce 'metric' card."""
    chart = determine_chart_archetype(
        col_names=["total_revenue"],
        col_types={"total_revenue": "float"},
        row_count=1,
    )
    assert chart == "metric"


def test_bar_chart_categorical_ranking():
    """Verify categorical rankings produce 'bar' chart."""
    chart = determine_chart_archetype(
        col_names=["category_name", "total_revenue"],
        col_types={"category_name": "text", "total_revenue": "float"},
        row_count=5,
        distinct_counts={"category_name": 5},
    )
    assert chart == "bar"


def test_donut_chart_proportions():
    """Verify low-cardinality status / payment method breakdown produces 'donut' chart."""
    chart = determine_chart_archetype(
        col_names=["status", "order_count"],
        col_types={"status": "text", "order_count": "int"},
        row_count=5,
        distinct_counts={"status": 5},
    )
    assert chart == "donut"


def test_line_chart_temporal_trend():
    """Verify monthly date series produces 'line' chart."""
    chart = determine_chart_archetype(
        col_names=["month", "monthly_revenue", "order_count"],
        col_types={"month": "text", "monthly_revenue": "float", "order_count": "int"},
        row_count=12,
    )
    assert chart == "line"


def test_area_chart_cumulative():
    """Verify cumulative revenue running sum produces 'area' chart."""
    chart = determine_chart_archetype(
        col_names=["month", "cumulative_revenue"],
        col_types={"month": "text", "cumulative_revenue": "float"},
        row_count=12,
    )
    assert chart == "area"


def test_table_view_multi_column():
    """Verify multi-column wide record sets produce 'table' view."""
    chart = determine_chart_archetype(
        col_names=["customer_id", "first_name", "last_name", "email", "city", "signup_date"],
        col_types={
            "customer_id": "int",
            "first_name": "text",
            "last_name": "text",
            "email": "text",
            "city": "text",
            "signup_date": "datetime",
        },
        row_count=50,
    )
    assert chart == "table"
