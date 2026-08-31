"""
backend/app/engine/insights.py
Executive Business Insights, Automated Chart Advisor, and Recharts Visualization Engine.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Tuple
from backend.app.models.schemas import ExecutiveSummary, MetricItem, ChartSpec


def determine_chart_archetype(
    col_names: List[str],
    col_types: Dict[str, str],
    row_count: int,
    distinct_counts: Optional[Dict[str, int]] = None,
) -> str:
    """
    Deterministic heuristic classifier for chart type selection.
    Aligned with enterprise benchmarking and Recharts visualizer.
    """
    distinct_counts = distinct_counts or {}

    # Rule 1: Single cell (1 row, 1 numeric col) -> Metric Card
    if row_count == 1:
        num_cols = [
            c for c in col_names
            if col_types.get(c, "") in ("numeric", "int", "float", "real", "decimal")
            or any(k in c.lower() for k in ("count", "sum", "total", "avg", "revenue", "spend", "cost", "margin", "rate", "pct"))
        ]
        if len(num_cols) >= 1 and len(col_names) <= 2:
            return "metric"

    # Rule 2: Temporal column present + numeric metric -> Line or Area Chart
    time_cols = [
        c for c in col_names
        if col_types.get(c, "") in ("date", "time", "datetime", "timestamp")
        or any(k in c.lower() for k in ("month", "year", "date", "day", "quarter", "hour", "signup_month", "order_day"))
    ]
    num_cols = [
        c for c in col_names
        if col_types.get(c, "") in ("numeric", "int", "float", "real", "decimal")
        or any(k in c.lower() for k in ("revenue", "sales", "amount", "spend", "price", "count", "orders", "total", "avg", "sum", "rate", "pct", "profit", "discount", "margin", "growth"))
    ]

    if time_cols and num_cols:
        # If cumulative or daily timeline -> area or line
        if any("cumul" in c.lower() or "daily" in c.lower() or "black_friday" in c.lower() for c in col_names):
            return "area"
        return "line"

    # Rule 3: Single Categorical + Single Numeric
    cat_cols = [c for c in col_names if c not in time_cols and c not in num_cols]
    if len(cat_cols) == 1 and len(num_cols) >= 1:
        cat_name = cat_cols[0]
        distinct_cnt = distinct_counts.get(cat_name, row_count)

        # Low cardinality share (2-6 distinct categories) -> Donut Chart
        if distinct_cnt <= 6 and any(k in cat_name.lower() for k in ("status", "method", "tier", "segment", "loyalty", "payment")):
            return "donut"

        # Ranking (7-30 categories) -> Bar Chart / Horizontal Bar
        if distinct_cnt <= 30:
            if any(k in cat_name.lower() for k in ("product", "name", "sku", "item")) and row_count >= 8:
                return "horizontal_bar"
            return "bar"

    # Rule 4: 2 Numeric Metrics + entity col (Correlation) -> Scatter
    if len(num_cols) >= 2 and len(col_names) <= 3 and row_count >= 10:
        if any("corr" in c.lower() for c in col_names):
            return "scatter"

    # Rule 5: High dimensional / multi-attribute -> Table
    return "table"


class InsightEngine:
    """Generates executive summaries, KPI cards, Recharts specifications, and follow-ups."""

    @staticmethod
    def infer_column_types(columns: List[str], rows: List[Dict[str, Any]]) -> Dict[str, str]:
        """Infer column data types from data values."""
        col_types = {}
        for col in columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ("date", "month", "year", "day", "time", "hour")):
                col_types[col] = "datetime"
            elif any(k in col_lower for k in ("price", "cost", "amount", "revenue", "spend", "rate", "pct", "margin", "profit", "total", "avg")):
                col_types[col] = "float"
            elif any(k in col_lower for k in ("count", "id", "quantity", "stock", "items")):
                col_types[col] = "int"
            else:
                # Inspect first non-null value
                val = next((r[col] for r in rows if r.get(col) is not None), None)
                if isinstance(val, (int,)):
                    col_types[col] = "int"
                elif isinstance(val, (float,)):
                    col_types[col] = "float"
                else:
                    col_types[col] = "text"
        return col_types

    @classmethod
    def generate_executive_summary(
        cls,
        question: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        sql: str
    ) -> ExecutiveSummary:
        """Create structured business executive summary with headline, KPIs, and takeaways."""
        if not rows:
            return ExecutiveSummary(
                headline="No matching analytical records found for the given criteria.",
                key_metrics=[],
                bullet_points=["The query executed successfully but returned 0 rows."],
                actionable_recommendations=["Broaden filter constraints or verify date ranges."],
            )

        key_metrics: List[MetricItem] = []
        bullet_points: List[str] = []
        recommendations: List[str] = []
        headline = ""

        first_row = rows[0]

        # Case 1: Single aggregate row (e.g. Total Revenue, Total Customers, Average Price)
        if len(rows) == 1:
            for col in columns:
                val = first_row[col]
                formatted_val = cls._format_val(col, val)
                label = col.replace("_", " ").title()
                key_metrics.append(MetricItem(label=label, value=formatted_val))
            
            main_metric = key_metrics[0]
            headline = f"{main_metric.label} stands at {main_metric.value}."
            bullet_points.append(f"Recorded aggregate metric: {main_metric.label} = {main_metric.value}.")
            recommendations.append("Track this baseline KPI against quarterly performance targets.")

        # Case 2: Grouped Ranking or Breakdown (e.g. Top Categories, Monthly Trends)
        else:
            cat_col = next((c for c in columns if any(k in c.lower() for c in ("name", "category", "status", "segment", "country", "tier", "month", "year", "method"))), columns[0])
            num_col = next((c for c in columns if c != cat_col and any(k in c.lower() for k in ("revenue", "amount", "count", "sales", "total", "spend", "profit", "avg"))), columns[-1] if len(columns) > 1 else columns[0])

            top_item = first_row[cat_col]
            top_val = first_row[num_col] if num_col in first_row else ""
            formatted_top_val = cls._format_val(num_col, top_val)

            headline = f"{top_item} leads the ranking with {formatted_top_val} in {num_col.replace('_', ' ')}."
            key_metrics.append(MetricItem(label=f"Top {cat_col.replace('_', ' ').title()}", value=str(top_item)))
            key_metrics.append(MetricItem(label=f"Leading {num_col.replace('_', ' ').title()}", value=formatted_top_val))

            if len(rows) > 1:
                runner_up = rows[1][cat_col]
                runner_val = cls._format_val(num_col, rows[1][num_col])
                bullet_points.append(f"Top performer: **{top_item}** ({formatted_top_val}).")
                bullet_points.append(f"Runner-up: **{runner_up}** ({runner_val}).")
                bullet_points.append(f"Total entries analyzed in result set: {len(rows)} rows.")
            
            recommendations.append(f"Focus strategic investments and inventory optimization on {top_item}.")
            recommendations.append("Conduct monthly cohort analysis to sustain competitive growth.")

        return ExecutiveSummary(
            headline=headline,
            key_metrics=key_metrics,
            bullet_points=bullet_points,
            actionable_recommendations=recommendations,
        )

    @classmethod
    def generate_chart_spec(
        cls,
        question: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        sql: str
    ) -> ChartSpec:
        """Construct Recharts visualization configuration."""
        if not rows or not columns:
            return ChartSpec(
                chart_type="table",
                title="Query Results Table",
                is_plottable=False,
            )

        col_types = cls.infer_column_types(columns, rows)
        row_cnt = len(rows)

        # Compute distinct counts
        distinct_counts = {}
        for c in columns:
            distinct_counts[c] = len(set(r.get(c) for r in rows if r.get(c) is not None))

        archetype = determine_chart_archetype(columns, col_types, row_cnt, distinct_counts)

        # Identify X and Y axes
        x_axis = None
        y_axis = None
        secondary_y = None
        num_cols = [c for c, t in col_types.items() if t in ("int", "float") or any(k in c.lower() for k in ("revenue", "sales", "amount", "total", "count", "profit", "margin", "rate", "spend"))]
        cat_cols = [c for c in columns if c not in num_cols]

        if archetype == "metric":
            x_axis = None
            y_axis = columns[0]
        elif archetype in ("line", "area"):
            x_axis = cat_cols[0] if cat_cols else columns[0]
            y_axis = num_cols[0] if num_cols else columns[-1]
            if len(num_cols) > 1:
                secondary_y = num_cols[1]
        elif archetype in ("bar", "horizontal_bar", "donut"):
            x_axis = cat_cols[0] if cat_cols else columns[0]
            y_axis = num_cols[0] if num_cols else columns[-1]
            if len(num_cols) > 1:
                secondary_y = num_cols[1]
        elif archetype == "scatter":
            x_axis = num_cols[0] if len(num_cols) > 0 else columns[0]
            y_axis = num_cols[1] if len(num_cols) > 1 else columns[1]
        else:
            x_axis = columns[0]
            y_axis = columns[1] if len(columns) > 1 else columns[0]

        # Format detection
        fmt = "standard"
        if y_axis and any(k in y_axis.lower() for k in ("revenue", "spend", "amount", "price", "cost", "profit", "total", "discount")):
            fmt = "currency"
        elif y_axis and any(k in y_axis.lower() for k in ("pct", "rate", "percentage", "growth")):
            fmt = "percentage"

        title = f"{question[:60]}..." if len(question) > 60 else question

        return ChartSpec(
            chart_type=archetype,
            title=title,
            description=f"Automated visualization showing {y_axis or 'metrics'} grouped by {x_axis or 'dimension'}.",
            x_axis=x_axis,
            y_axis=y_axis,
            secondary_y_axis=secondary_y,
            is_plottable=archetype != "table",
            format=fmt,
        )

    @staticmethod
    def generate_followups(question: str, columns: List[str], rows: List[Dict[str, Any]]) -> List[str]:
        """Generate 3 contextual follow-up questions."""
        q_lower = question.lower()
        followups = []

        if "category" in q_lower or "categories" in q_lower:
            followups.append("What are the top 10 best-selling products within the leading category?")
            followups.append("Show the monthly revenue trend for these categories in 2024.")
            followups.append("What is the average review rating and discount rate by category?")
        elif "customer" in q_lower or "loyalty" in q_lower or "clv" in q_lower:
            followups.append("What is the average order value (AOV) across different customer loyalty tiers?")
            followups.append("Which customer acquisition channels produce the highest lifetime value?")
            followups.append("Show the geographic breakdown of customers by top spending states.")
        elif "inventory" in q_lower or "stock" in q_lower:
            followups.append("Which products currently have stock levels below their reorder threshold?")
            followups.append("What is the total inventory valuation stored in each regional warehouse?")
            followups.append("Show suppliers with the highest average product fulfillment rating.")
        elif "2024" in q_lower or "trend" in q_lower or "month" in q_lower:
            followups.append("Compare quarterly revenue between 2023 and 2024.")
            followups.append("What was the day-of-week distribution of completed order volume?")
            followups.append("What was the daily revenue during Black Friday week in November 2024?")
        else:
            followups.append("What are the top 5 product categories by total sales revenue?")
            followups.append("Show monthly sales revenue trend for completed orders in 2024.")
            followups.append("What is the Customer Lifetime Value (CLV) distribution across loyalty tiers?")

        return followups[:3]

    @staticmethod
    def _format_val(col_name: str, val: Any) -> str:
        """Format numbers nicely for summaries and metrics."""
        if val is None:
            return "N/A"
        col_lower = col_name.lower()
        if isinstance(val, (int, float)):
            if any(k in col_lower for k in ("revenue", "spend", "amount", "price", "cost", "profit", "discount", "clv", "total_price")):
                if abs(val) >= 1_000_000:
                    return f"${val / 1_000_000:.2f}M"
                if abs(val) >= 1_000:
                    return f"${val:,.2f}"
                return f"${val:.2f}"
            elif any(k in col_lower for k in ("pct", "rate", "percentage", "growth")):
                return f"{val:.1f}%"
            elif isinstance(val, int) or val.is_integer():
                return f"{int(val):,}"
            else:
                return f"{val:,.2f}"
        return str(val)
