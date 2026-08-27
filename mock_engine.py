"""
Mock Natural Language to SQL (NL-to-SQL) Simulation Engine.
Provides rule-based intent parsing, dynamic entity extraction, SQL query formatting,
realistic structured Pandas DataFrames, and 3-part natural language explanations.
Zero external API keys or live database connections required.
"""

import re
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import pandas as pd


@dataclass
class NLtoSQLResult:
    """Structured result returned by the Mock NL-to-SQL Engine."""
    user_query: str
    intent: str
    explanation: str
    sql_query: str
    dataframe: pd.DataFrame
    execution_time_ms: float
    row_count: int
    dialect: str = "PostgreSQL"
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggested_followups: List[str] = field(default_factory=list)

    @property
    def sql(self) -> str:
        """Alias for sql_query."""
        return self.sql_query

    @property
    def df(self) -> pd.DataFrame:
        """Alias for dataframe."""
        return self.dataframe

    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access for maximum flexibility."""
        alias_map = {
            "sql": "sql_query",
            "df": "dataframe",
            "explanation": "explanation",
            "content": "explanation",
            "user_query": "user_query",
            "intent": "intent",
            "sql_query": "sql_query",
            "dataframe": "dataframe",
            "execution_time_ms": "execution_time_ms",
            "row_count": "row_count",
            "dialect": "dialect",
            "metrics": "metrics",
            "suggested_followups": "suggested_followups",
        }
        target_attr = alias_map.get(key, key)
        if hasattr(self, target_attr):
            return getattr(self, target_attr)
        raise KeyError(f"Key '{key}' not found in NLtoSQLResult")

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method."""
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to standard dictionary."""
        return {
            "user_query": self.user_query,
            "intent": self.intent,
            "explanation": self.explanation,
            "sql_query": self.sql_query,
            "sql": self.sql_query,
            "dataframe": self.dataframe,
            "df": self.dataframe,
            "execution_time_ms": self.execution_time_ms,
            "row_count": self.row_count,
            "dialect": self.dialect,
            "metrics": self.metrics,
            "suggested_followups": self.suggested_followups,
        }


class MockNLtoSQLEngine:
    """Offline Mock NL-to-SQL Query Generator and Data Simulator."""

    def __init__(self, default_dialect: str = "PostgreSQL"):
        self.default_dialect = default_dialect

    def process_query(self, prompt: str, dialect: Optional[str] = None) -> NLtoSQLResult:
        """
        Processes a natural language string and returns a structured NLtoSQLResult.
        Guaranteed to never raise uncaught exceptions.
        """
        active_dialect = dialect or self.default_dialect
        start_time = time.perf_counter()

        cleaned_prompt = (prompt or "").strip()
        if not cleaned_prompt:
            return self._handle_empty_query(active_dialect)

        # Route query to corresponding intent handler
        intent, params = self._classify_intent(cleaned_prompt)

        handler_map = {
            "top_products": self._generate_top_products,
            "revenue_trend": self._generate_revenue_trend,
            "top_customers": self._generate_top_customers,
            "regional_sales": self._generate_regional_sales,
            "inventory_status": self._generate_inventory_status,
            "order_fulfillment": self._generate_order_fulfillment,
            "category_breakdown": self._generate_category_breakdown,
        }

        handler = handler_map.get(intent, self._generate_fallback)
        result_payload = handler(cleaned_prompt, params, active_dialect)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000 + random.uniform(12.0, 28.0), 1)

        return NLtoSQLResult(
            user_query=cleaned_prompt,
            intent=intent,
            explanation=result_payload["explanation"],
            sql_query=result_payload["sql"],
            dataframe=result_payload["df"],
            execution_time_ms=elapsed_ms,
            row_count=len(result_payload["df"]),
            dialect=active_dialect,
            metrics=result_payload.get("metrics", {}),
            suggested_followups=result_payload.get("suggested_followups", [])
        )

    def _classify_intent(self, prompt: str) -> tuple[str, Dict[str, Any]]:
        """Classifies user intent and extracts dynamic parameters like limits and years."""
        p_lower = prompt.lower()
        params: Dict[str, Any] = {}

        # Extract numerical limit (e.g. "top 10", "top 5", "first 20")
        limit_match = re.search(r"\b(?:top|first|limit)\s+(\d+)\b", p_lower)
        params["limit"] = int(limit_match.group(1)) if limit_match else 10

        # Extract year (e.g. "in 2025", "2024", "2026")
        year_match = re.search(r"\b(202[0-9])\b", p_lower)
        params["year"] = int(year_match.group(1)) if year_match else 2025

        # 1. Top products by revenue / best selling products
        if re.search(r"\b(?:top|best[\s\-]selling|highest\s+revenue|popular|leading)\s+(?:\d+\s+)?(?:products?|items?|skus?)\b", p_lower) or \
           (re.search(r"\bproducts?\b", p_lower) and re.search(r"\b(?:revenue|sales|selling)\b", p_lower)):
            return "top_products", params

        # 2. Monthly revenue trend / sales over time
        if re.search(r"\b(?:month(?:ly)?|quarter(?:ly)?|trend|growth|over\s+time|history)\b", p_lower) and \
           re.search(r"\b(?:revenue|sales|financials?|income)\b", p_lower):
            return "revenue_trend", params

        # 3. Top customers / VIP clients / Lifetime value
        if re.search(r"\b(?:customers?|clients?|accounts?|vips?|buyers?)\b", p_lower) and \
           re.search(r"\b(?:top|highest|lifetime\s+value|ltv|spend(?:ing)?|value|tier)\b", p_lower):
            return "top_customers", params

        # 4. Regional sales / geographic breakdown
        if re.search(r"\b(?:region(?:al)?|countr(?:y|ies)|territor(?:y|ies)|geograph(?:y|ic)|shipping\s+region)\b", p_lower):
            return "regional_sales", params

        # 5. Inventory status / low stock / warehouse
        if re.search(r"\b(?:inventory|stock|reorder|warehouse|out\s+of\s+stock|low\s+stock|threshold)\b", p_lower):
            return "inventory_status", params

        # 6. Order fulfillment / order statuses
        if re.search(r"\b(?:order\s+status(?:es)?|fulfillment|pending|refund(?:s|ed)?|shipped|delivery)\b", p_lower):
            return "order_fulfillment", params

        # 7. Category breakdown
        if re.search(r"\b(?:category|categories|product\s+mix|segmentation\s+by\s+category)\b", p_lower):
            return "category_breakdown", params

        # Generic fallback
        return "fallback_generic", params

    def _generate_top_products(self, prompt: str, params: Dict[str, Any], dialect: str) -> Dict[str, Any]:
        limit = min(max(params.get("limit", 10), 1), 50)
        year = params.get("year", 2025)

        sql = f"""-- Dialect: {dialect}
-- Intent: Top {limit} Products by Revenue ({year})
SELECT 
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_rate)), 2) AS total_revenue,
    ROUND(AVG(oi.unit_price), 2) AS avg_unit_price,
    ROUND(AVG(oi.discount_rate) * 100.0, 1) AS avg_discount_pct
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_date >= '{year}-01-01' 
  AND o.order_date <= '{year}-12-31'
  AND o.status = 'Completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT {limit};"""

        all_products = [
            {"Rank": 1, "Product Name": "CloudScale Enterprise Server v4", "Category": "Cloud Infrastructure", "Units Sold": 4820, "Total Revenue ($)": 1842500.00, "Avg Unit Price ($)": 399.00, "Avg Discount (%)": 4.2},
            {"Rank": 2, "Product Name": "AI Analytics Neural Suite", "Category": "AI & Analytics", "Units Sold": 3150, "Total Revenue ($)": 1520300.00, "Avg Unit Price ($)": 499.00, "Avg Discount (%)": 3.1},
            {"Rank": 3, "Product Name": "CyberShield Perimeter Defense", "Category": "Cyber Security", "Units Sold": 2890, "Total Revenue ($)": 1290400.00, "Avg Unit Price ($)": 450.00, "Avg Discount (%)": 0.8},
            {"Rank": 4, "Product Name": "QuantumDB Distributed Engine", "Category": "Enterprise Software", "Units Sold": 1940, "Total Revenue ($)": 1180900.00, "Avg Unit Price ($)": 620.00, "Avg Discount (%)": 1.9},
            {"Rank": 5, "Product Name": "HyperMesh Edge Router X9", "Category": "Hardware Appliance", "Units Sold": 3410, "Total Revenue ($)": 945600.00, "Avg Unit Price ($)": 285.00, "Avg Discount (%)": 2.6},
            {"Rank": 6, "Product Name": "DataVault Encrypted SAN Array", "Category": "Hardware Appliance", "Units Sold": 1120, "Total Revenue ($)": 872100.00, "Avg Unit Price ($)": 790.00, "Avg Discount (%)": 1.5},
            {"Rank": 7, "Product Name": "ZeroTrust Identity Gateway", "Category": "Cyber Security", "Units Sold": 2650, "Total Revenue ($)": 780250.00, "Avg Unit Price ($)": 310.00, "Avg Discount (%)": 5.0},
            {"Rank": 8, "Product Name": "AutoML Pipeline Accelerators", "Category": "AI & Analytics", "Units Sold": 1830, "Total Revenue ($)": 695400.00, "Avg Unit Price ($)": 395.00, "Avg Discount (%)": 3.9},
            {"Rank": 9, "Product Name": "OmniFlow BPM Platform", "Category": "Enterprise Software", "Units Sold": 1540, "Total Revenue ($)": 540800.00, "Avg Unit Price ($)": 360.00, "Avg Discount (%)": 2.5},
            {"Rank": 10, "Product Name": "CloudSync Global Replicator", "Category": "Cloud Infrastructure", "Units Sold": 2100, "Total Revenue ($)": 485200.00, "Avg Unit Price ($)": 240.00, "Avg Discount (%)": 3.7},
            {"Rank": 11, "Product Name": "LogSentinel SIEM Collector", "Category": "Cyber Security", "Units Sold": 1420, "Total Revenue ($)": 426000.00, "Avg Unit Price ($)": 310.00, "Avg Discount (%)": 3.0},
            {"Rank": 12, "Product Name": "API Gateway Express Pro", "Category": "Enterprise Software", "Units Sold": 1980, "Total Revenue ($)": 396000.00, "Avg Unit Price ($)": 205.00, "Avg Discount (%)": 2.4},
            {"Rank": 13, "Product Name": "VectorSearch Cluster Node", "Category": "AI & Analytics", "Units Sold": 940, "Total Revenue ($)": 376000.00, "Avg Unit Price ($)": 410.00, "Avg Discount (%)": 2.1},
            {"Rank": 14, "Product Name": "EdgeGuard Micro Firewall", "Category": "Hardware Appliance", "Units Sold": 2250, "Total Revenue ($)": 337500.00, "Avg Unit Price ($)": 155.00, "Avg Discount (%)": 3.2},
            {"Rank": 15, "Product Name": "AuditTrail Compliance Hub", "Category": "Enterprise Software", "Units Sold": 1100, "Total Revenue ($)": 319000.00, "Avg Unit Price ($)": 295.00, "Avg Discount (%)": 1.7},
        ]

        # Slice to requested limit (default 10)
        selected_records = all_products[:limit]
        # If limit exceeds available list, generate indexed extensions
        if len(selected_records) < limit:
            for idx in range(len(selected_records) + 1, limit + 1):
                selected_records.append({
                    "Rank": idx,
                    "Product Name": f"Enterprise Addon Module #{idx}",
                    "Category": "Enterprise Software",
                    "Units Sold": max(500 - idx * 10, 50),
                    "Total Revenue ($)": round(max(300000.0 - idx * 6000.0, 25000.0), 2),
                    "Avg Unit Price ($)": 180.00,
                    "Avg Discount (%)": 2.0
                })

        df = pd.DataFrame(selected_records)
        total_rev = df["Total Revenue ($)"].sum()
        top_item = df.iloc[0]["Product Name"]

        explanation = f"""### 📊 Executive Summary
In **{year}**, the top **{len(df)} products** generated a cumulative gross revenue of **${total_rev:,.2f}** across completed enterprise orders. The #1 revenue driver was **{top_item}** (${df.iloc[0]['Total Revenue ($)']:,.2f}), representing strong adoption across the {df.iloc[0]['Category']} product category.

---

### 🔍 Query Construction & Execution Logic
1. **Tables & Relations**:
   - `products` (Product metadata & SKU definitions)
   - `order_items` (Individual line items, quantities, and discount rates)
   - `orders` (Transaction metadata, completion status, and transaction timestamps)
2. **Join Conditions**:
   - `products.product_id = order_items.product_id` (N:1 join)
   - `order_items.order_id = orders.order_id` (N:1 join)
3. **Filtering Rules**:
   - `orders.order_date` strictly bounded between `{year}-01-01` and `{year}-12-31`.
   - `orders.status = 'Completed'` to exclude refunded, processing, or cancelled transactions.
4. **Aggregation & Ordering**:
   - Grouped by `product_id`, `product_name`, and `category`.
   - Calculated discounted total revenue via `SUM(quantity * unit_price * (1 - discount_rate))`.
   - Ordered by `total_revenue DESC` and restricted to `LIMIT {limit}`."""

        return {
            "sql": sql,
            "df": df,
            "explanation": explanation,
            "metrics": {"total_revenue": total_rev, "top_product": top_item},
            "suggested_followups": [
                f"Show monthly revenue trend for {top_item} in {year}",
                "Break down top product revenue by customer segment",
                "Show inventory stock levels for these top 10 products"
            ]
        }

    def _generate_revenue_trend(self, prompt: str, params: Dict[str, Any], dialect: str) -> Dict[str, Any]:
        year = params.get("year", 2025)

        sql = f"""-- Dialect: {dialect}
-- Intent: Monthly Revenue Trend & MoM Growth ({year})
SELECT 
    TO_CHAR(order_date, 'YYYY-MM') AS month,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS active_customers,
    ROUND(SUM(total_amount), 2) AS gross_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    ROUND(
        (SUM(total_amount) - LAG(SUM(total_amount)) OVER (ORDER BY TO_CHAR(order_date, 'YYYY-MM'))) /
        NULLIF(LAG(SUM(total_amount)) OVER (ORDER BY TO_CHAR(order_date, 'YYYY-MM')), 0) * 100.0, 2
    ) AS mom_growth_pct
FROM orders
WHERE order_date >= '{year}-01-01' 
  AND order_date <= '{year}-12-31'
  AND status = 'Completed'
GROUP BY TO_CHAR(order_date, 'YYYY-MM')
ORDER BY month ASC;"""

        monthly_data = [
            {"Month": f"{year}-01", "Total Orders": 412, "Active Customers": 320, "Gross Revenue ($)": 642300.00, "Avg Order Value ($)": 1558.98, "MoM Growth (%)": 0.0},
            {"Month": f"{year}-02", "Total Orders": 435, "Active Customers": 341, "Gross Revenue ($)": 681400.00, "Avg Order Value ($)": 1566.44, "MoM Growth (%)": 6.09},
            {"Month": f"{year}-03", "Total Orders": 489, "Active Customers": 378, "Gross Revenue ($)": 752100.00, "Avg Order Value ($)": 1538.04, "MoM Growth (%)": 10.38},
            {"Month": f"{year}-04", "Total Orders": 472, "Active Customers": 365, "Gross Revenue ($)": 738900.00, "Avg Order Value ($)": 1565.47, "MoM Growth (%)": -1.75},
            {"Month": f"{year}-05", "Total Orders": 515, "Active Customers": 395, "Gross Revenue ($)": 814200.00, "Avg Order Value ($)": 1580.97, "MoM Growth (%)": 10.19},
            {"Month": f"{year}-06", "Total Orders": 540, "Active Customers": 412, "Gross Revenue ($)": 856000.00, "Avg Order Value ($)": 1585.19, "MoM Growth (%)": 5.13},
            {"Month": f"{year}-07", "Total Orders": 528, "Active Customers": 405, "Gross Revenue ($)": 841500.00, "Avg Order Value ($)": 1593.75, "MoM Growth (%)": -1.69},
            {"Month": f"{year}-08", "Total Orders": 562, "Active Customers": 430, "Gross Revenue ($)": 894300.00, "Avg Order Value ($)": 1591.28, "MoM Growth (%)": 6.27},
            {"Month": f"{year}-09", "Total Orders": 580, "Active Customers": 448, "Gross Revenue ($)": 928400.00, "Avg Order Value ($)": 1600.69, "MoM Growth (%)": 3.81},
            {"Month": f"{year}-10", "Total Orders": 614, "Active Customers": 472, "Gross Revenue ($)": 985100.00, "Avg Order Value ($)": 1604.40, "MoM Growth (%)": 6.11},
            {"Month": f"{year}-11", "Total Orders": 695, "Active Customers": 520, "Gross Revenue ($)": 1120400.00, "Avg Order Value ($)": 1612.09, "MoM Growth (%)": 13.73},
            {"Month": f"{year}-12", "Total Orders": 745, "Active Customers": 560, "Gross Revenue ($)": 1210800.00, "Avg Order Value ($)": 1625.23, "MoM Growth (%)": 8.07},
        ]

        df = pd.DataFrame(monthly_data)
        annual_rev = df["Gross Revenue ($)"].sum()
        total_orders = df["Total Orders"].sum()

        explanation = f"""### 📊 Executive Summary
In **{year}**, total annual revenue reached **${annual_rev:,.2f}** across **{total_orders:,} completed transactions**. Revenue exhibited consistent upward momentum, expanding from **$642.3k in January** to a peak of **$1.21M in December** (+88.5% annual expansion), with Q4 contributing 31.6% of overall fiscal performance.

---

### 🔍 Query Construction & Execution Logic
1. **Temporal Grouping**:
   - Extracted year-month buckets via `TO_CHAR(order_date, 'YYYY-MM')`.
2. **Key Metric Calculations**:
   - `COUNT(DISTINCT order_id)` for total transactional volume.
   - `COUNT(DISTINCT customer_id)` for unique active monthly buyers.
   - `SUM(total_amount)` for monthly gross revenue.
3. **Window Analytical Function**:
   - `LAG(SUM(total_amount)) OVER (ORDER BY month)` utilized to compute precise Month-over-Month (MoM) growth trajectory."""

        return {
            "sql": sql,
            "df": df,
            "explanation": explanation,
            "metrics": {"annual_revenue": annual_rev, "total_orders": total_orders},
            "suggested_followups": [
                f"Compare Q4 {year} vs Q4 {year-1} performance",
                "Which customer segments drove the December revenue peak?",
                "Show average order value distribution by payment method"
            ]
        }

    def _generate_top_customers(self, prompt: str, params: Dict[str, Any], dialect: str) -> Dict[str, Any]:
        limit = min(max(params.get("limit", 5), 1), 25)

        sql = f"""-- Dialect: {dialect}
-- Intent: Top {limit} High-Value Enterprise Customers (LTV & Transaction History)
SELECT 
    c.customer_id,
    c.company_name,
    c.segment,
    c.tier,
    c.country,
    COUNT(o.order_id) AS completed_orders,
    ROUND(SUM(o.total_amount), 2) AS total_spend,
    MAX(o.order_date) AS last_order_date
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'Completed'
GROUP BY c.customer_id, c.company_name, c.segment, c.tier, c.country
ORDER BY total_spend DESC
LIMIT {limit};"""

        customers_data = [
            {"Customer ID": 1042, "Company Name": "Apex Global Technologies", "Segment": "Enterprise", "Tier": "Platinum", "Country": "United States", "Completed Orders": 184, "Total Spend ($)": 945200.00, "Last Order Date": "2025-12-28"},
            {"Customer ID": 1018, "Company Name": "Horizon Financial Partners", "Segment": "Enterprise", "Tier": "Platinum", "Country": "United Kingdom", "Completed Orders": 142, "Total Spend ($)": 812400.00, "Last Order Date": "2025-12-21"},
            {"Customer ID": 1089, "Company Name": "Nexus Dynamics Inc.", "Segment": "Enterprise", "Tier": "Platinum", "Country": "Germany", "Completed Orders": 126, "Total Spend ($)": 745900.00, "Last Order Date": "2025-12-19"},
            {"Customer ID": 1033, "Company Name": "Titan Global Logistics", "Segment": "Enterprise", "Tier": "Gold", "Country": "Canada", "Completed Orders": 98, "Total Spend ($)": 628300.00, "Last Order Date": "2025-12-15"},
            {"Customer ID": 1115, "Company Name": "Orion HealthTech Systems", "Segment": "Enterprise", "Tier": "Gold", "Country": "Australia", "Completed Orders": 91, "Total Spend ($)": 591700.00, "Last Order Date": "2025-12-24"},
            {"Customer ID": 1074, "Company Name": "Vanguard Cloud Computing", "Segment": "Mid-Market", "Tier": "Gold", "Country": "United States", "Completed Orders": 84, "Total Spend ($)": 512000.00, "Last Order Date": "2025-12-10"},
            {"Customer ID": 1056, "Company Name": "Solaris Energy Solutions", "Segment": "Enterprise", "Tier": "Silver", "Country": "France", "Completed Orders": 76, "Total Spend ($)": 468200.00, "Last Order Date": "2025-12-05"},
            {"Customer ID": 1120, "Company Name": "AeroSpace Matrix Corp", "Segment": "Enterprise", "Tier": "Silver", "Country": "Japan", "Completed Orders": 69, "Total Spend ($)": 431000.00, "Last Order Date": "2025-11-29"},
        ]

        selected_records = customers_data[:limit]
        if len(selected_records) < limit:
            for idx in range(len(selected_records) + 1, limit + 1):
                selected_records.append({
                    "Customer ID": 1100 + idx,
                    "Company Name": f"Strategic Enterprise Client #{idx}",
                    "Segment": "Enterprise",
                    "Tier": "Silver",
                    "Country": "United States",
                    "Completed Orders": max(60 - idx * 2, 20),
                    "Total Spend ($)": round(max(400000.0 - idx * 15000.0, 100000.0), 2),
                    "Last Order Date": "2025-11-15"
                })

        df = pd.DataFrame(selected_records)
        top_client = df.iloc[0]["Company Name"]
        top_spend = df.iloc[0]["Total Spend ($)"]

        explanation = f"""### 📊 Executive Summary
The top **{len(df)} high-value customers** account for **${df['Total Spend ($)'].sum():,.2f}** in cumulative spend. **{top_client}** leads with **${top_spend:,.2f}** across {df.iloc[0]['Completed Orders']} orders. 100% of the top 3 clients belong to the **Platinum Enterprise** tier with active orders within the last 30 days.

---

### 🔍 Query Construction & Execution Logic
1. **Join Structure**:
   - `customers` (Account metadata, tier, segment) joined with `orders` on `customer_id`.
2. **Aggregations**:
   - `COUNT(o.order_id)` computes transaction frequency.
   - `SUM(o.total_amount)` computes cumulative customer lifetime value (LTV).
   - `MAX(o.order_date)` identifies most recent transaction recency."""

        return {
            "sql": sql,
            "df": df,
            "explanation": explanation,
            "suggested_followups": [
                f"Show product purchase history for {top_client}",
                "Break down customer count and total spend by Tier (Platinum/Gold/Silver)",
                "Identify enterprise accounts with no orders in past 90 days"
            ]
        }

    def _generate_regional_sales(self, prompt: str, params: Dict[str, Any], dialect: str) -> Dict[str, Any]:
        sql = f"""-- Dialect: {dialect}
-- Intent: Regional Revenue Distribution & Order Share
SELECT 
    o.shipping_region,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(100.0 * SUM(o.total_amount) / SUM(SUM(o.total_amount)) OVER(), 2) AS revenue_share_pct,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value
FROM orders o
WHERE o.status = 'Completed'
GROUP BY o.shipping_region
ORDER BY total_revenue DESC;"""

        regional_data = [
            {"Shipping Region": "North America", "Total Orders": 3280, "Unique Customers": 1840, "Total Revenue ($)": 5214800.00, "Revenue Share (%)": 48.65, "Avg Order Value ($)": 1589.88},
            {"Shipping Region": "EMEA (Europe & Middle East)", "Total Orders": 1940, "Unique Customers": 1120, "Total Revenue ($)": 3021400.00, "Revenue Share (%)": 28.19, "Avg Order Value ($)": 1557.42},
            {"Shipping Region": "APAC (Asia-Pacific)", "Total Orders": 1280, "Unique Customers": 790, "Total Revenue ($)": 1845600.00, "Revenue Share (%)": 17.22, "Avg Order Value ($)": 1441.88},
            {"Shipping Region": "LATAM (Latin America)", "Total Orders": 420, "Unique Customers": 260, "Total Revenue ($)": 637200.00, "Revenue Share (%)": 5.94, "Avg Order Value ($)": 1517.14},
        ]

        df = pd.DataFrame(regional_data)
        total_global = df["Total Revenue ($)"].sum()

        explanation = f"""### 📊 Executive Summary
Global completed order revenue stands at **${total_global:,.2f}**. **North America** represents our dominant market, generating **$5.21M (48.65%)**, followed by **EMEA at $3.02M (28.19%)** and **APAC at $1.85M (17.22%)**. Average order values remain consistent across all major geographies at ~$1,550.

---

### 🔍 Query Construction & Execution Logic
1. **Grouping Dimension**: `orders.shipping_region`.
2. **Window Metric**: `SUM(total_amount) / SUM(SUM(total_amount)) OVER()` computes global revenue share percentage.
3. **Volume Metrics**: Distinct counting of orders and active purchasing organizations per territory."""

        return {
            "sql": sql,
            "df": df,
            "explanation": explanation,
            "suggested_followups": [
                "Show top products sold in North America vs EMEA",
                "What is the shipping turnaround time per region?",
                "Which countries in APAC have the highest growth rate?"
            ]
        }

    def _generate_inventory_status(self, prompt: str, params: Dict[str, Any], dialect: str) -> Dict[str, Any]:
        sql = f"""-- Dialect: {dialect}
-- Intent: Low Stock Inventory Alerts & Reorder Status
SELECT 
    product_id,
    product_name,
    category,
    stock_quantity,
    reorder_threshold,
    unit_price,
    CASE 
        WHEN stock_quantity = 0 THEN 'CRITICAL: Out of Stock'
        WHEN stock_quantity <= reorder_threshold / 2 THEN 'HIGH ALERT: Urgent Reorder'
        WHEN stock_quantity <= reorder_threshold THEN 'WARNING: Low Stock'
        ELSE 'HEALTHY'
    END AS stock_status
FROM products
WHERE stock_quantity <= reorder_threshold
ORDER BY stock_quantity ASC;"""

        inventory_data = [
            {"Product ID": 105, "Product Name": "HyperMesh Edge Router X9", "Category": "Hardware Appliance", "Stock Quantity": 0, "Reorder Threshold": 150, "Unit Price ($)": 285.00, "Stock Status": "CRITICAL: Out of Stock"},
            {"Product ID": 112, "Product Name": "DataVault Encrypted SAN Array", "Category": "Hardware Appliance", "Stock Quantity": 14, "Reorder Threshold": 80, "Unit Price ($)": 790.00, "Stock Status": "HIGH ALERT: Urgent Reorder"},
            {"Product ID": 101, "Product Name": "CloudScale Enterprise Server v4", "Category": "Cloud Infrastructure", "Stock Quantity": 28, "Reorder Threshold": 100, "Unit Price ($)": 399.00, "Stock Status": "HIGH ALERT: Urgent Reorder"},
            {"Product ID": 119, "Product Name": "EdgeGuard Micro Firewall", "Category": "Hardware Appliance", "Stock Quantity": 45, "Reorder Threshold": 120, "Unit Price ($)": 155.00, "Stock Status": "HIGH ALERT: Urgent Reorder"},
            {"Product ID": 108, "Product Name": "ZeroTrust Identity Gateway", "Category": "Cyber Security", "Stock Quantity": 62, "Reorder Threshold": 90, "Unit Price ($)": 310.00, "Stock Status": "WARNING: Low Stock"},
            {"Product ID": 115, "Product Name": "AuditTrail Compliance Hub", "Category": "Enterprise Software", "Stock Quantity": 74, "Reorder Threshold": 85, "Unit Price ($)": 295.00, "Stock Status": "WARNING: Low Stock"},
        ]

        df = pd.DataFrame(inventory_data)
        out_of_stock_count = (df["Stock Quantity"] == 0).sum()

        explanation = f"""### 📊 Executive Summary
Identified **{len(df)} SKUs** at or below their designated safety reorder thresholds. **{out_of_stock_count} item is currently out of stock** (*HyperMesh Edge Router X9*), while 3 high-volume hardware appliances require immediate supplier purchase orders to prevent order fulfillment bottlenecks.

---

### 🔍 Query Construction & Execution Logic
1. **Condition**: `WHERE stock_quantity <= reorder_threshold`.
2. **Classification Logic**: Multi-tiered `CASE WHEN` statement evaluating inventory depletion severity.
3. **Sorting**: Ordered by `stock_quantity ASC` to highlight zero-stock and high-risk items first."""

        return {
            "sql": sql,
            "df": df,
            "explanation": explanation,
            "suggested_followups": [
                "Which open orders contain out-of-stock items?",
                "Show primary suppliers and lead times for low stock products",
                "Estimate total procurement cost to replenish inventory to safe levels"
            ]
        }

    def _generate_order_fulfillment(self, prompt: str, params: Dict[str, Any], dialect: str) -> Dict[str, Any]:
        sql = f"""-- Dialect: {dialect}
-- Intent: Order Fulfillment Lifecycle & Status Breakdown
SELECT 
    status AS order_status,
    COUNT(*) AS total_orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS status_share_pct,
    ROUND(SUM(total_amount), 2) AS total_volume_usd,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
GROUP BY status
ORDER BY total_orders DESC;"""

        status_data = [
            {"Order Status": "Completed", "Total Orders": 6920, "Status Share (%)": 72.84, "Total Volume ($)": 10719000.00, "Avg Order Value ($)": 1549.00},
            {"Order Status": "Shipped (In Transit)", "Total Orders": 1340, "Status Share (%)": 14.11, "Total Volume ($)": 2090400.00, "Avg Order Value ($)": 1560.00},
            {"Order Status": "Processing (Warehouse)", "Total Orders": 790, "Status Share (%)": 8.32, "Total Volume ($)": 1216600.00, "Avg Order Value ($)": 1540.00},
            {"Order Status": "Refunded", "Total Orders": 280, "Status Share (%)": 2.95, "Total Volume ($)": 414400.00, "Avg Order Value ($)": 1480.00},
            {"Order Status": "Cancelled", "Total Orders": 170, "Status Share (%)": 1.79, "Total Volume ($)": 251600.00, "Avg Order Value ($)": 1480.00},
        ]

        df = pd.DataFrame(status_data)

        explanation = f"""### 📊 Executive Summary
Overall transaction fulfillment health is robust with **86.95% of orders successfully completed or in transit**. Return/refund rates are contained at **2.95%**, while active fulfillment queues represent 8.32% (790 orders) undergoing warehouse dispatch.

---

### 🔍 Query Construction & Execution Logic
1. **Grouping Dimension**: `orders.status`.
2. **Aggregations**: Calculated volume, dollar value, average ticket size, and global distribution percentage."""

        return {
            "sql": sql,
            "df": df,
            "explanation": explanation,
            "suggested_followups": [
                "What is the average processing time for orders in transit?",
                "Break down refunded orders by product category",
                "Show orders pending fulfillment for over 48 hours"
            ]
        }

    def _generate_category_breakdown(self, prompt: str, params: Dict[str, Any], dialect: str) -> Dict[str, Any]:
        sql = f"""-- Dialect: {dialect}
-- Intent: Product Category Performance & Revenue Mix
SELECT 
    p.category,
    COUNT(DISTINCT p.product_id) AS product_count,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_rate)), 2) AS category_revenue,
    ROUND(AVG(oi.unit_price), 2) AS avg_unit_price,
    ROUND(100.0 * SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_rate)) / 
          SUM(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_rate))) OVER(), 2) AS revenue_share_pct
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY p.category
ORDER BY category_revenue DESC;"""

        cat_data = [
            {"Category": "Cloud Infrastructure", "Product Count": 14, "Total Units Sold": 8420, "Category Revenue ($)": 3840500.00, "Avg Unit Price ($)": 380.00, "Revenue Share (%)": 35.83},
            {"Category": "Enterprise Software", "Product Count": 22, "Total Units Sold": 7150, "Category Revenue ($)": 2980200.00, "Avg Unit Price ($)": 415.00, "Revenue Share (%)": 27.80},
            {"Category": "AI & Analytics", "Product Count": 12, "Total Units Sold": 5420, "Category Revenue ($)": 2210800.00, "Avg Unit Price ($)": 440.00, "Revenue Share (%)": 20.62},
            {"Category": "Cyber Security", "Product Count": 10, "Total Units Sold": 3890, "Category Revenue ($)": 1687500.00, "Avg Unit Price ($)": 360.00, "Avg Discount (%)": 15.75},
        ]

        df = pd.DataFrame(cat_data)

        explanation = f"""### 📊 Executive Summary
The portfolio is led by **Cloud Infrastructure** generating **$3.84M (35.83%)** and **Enterprise Software at $2.98M (27.80%)**. AI & Analytics demonstrated rapid growth, capturing over 20% of commercial revenue.

---

### 🔍 Query Construction & Execution Logic
1. **Relations**: `products` joined to `order_items` and `orders`.
2. **Aggregations**: Calculated units sold, gross revenue after discounts, and portfolio revenue share percentage."""

        return {
            "sql": sql,
            "df": df,
            "explanation": explanation,
            "suggested_followups": [
                "Show top performing individual products in Cloud Infrastructure",
                "What is the average discount rate per category?",
                "Which category has the highest customer repeat purchase rate?"
            ]
        }

    def _generate_fallback(self, prompt: str, params: Dict[str, Any], dialect: str) -> Dict[str, Any]:
        """Intelligent, resilient fallback generator for arbitrary custom prompts."""
        year = params.get("year", 2025)
        limit = params.get("limit", 5)

        # Detect keywords in query to shape synthetic SQL
        p_lower = prompt.lower()
        if "customer" in p_lower:
            primary_table = "customers"
            select_cols = "c.customer_id, c.company_name, c.segment, c.lifetime_value"
            group_cols = "c.customer_id, c.company_name, c.segment, c.lifetime_value"
            sample_df = pd.DataFrame([
                {"Customer ID": 1001, "Company Name": "Alpha Enterprise Systems", "Segment": "Enterprise", "Metric Value": 421000.00, "Period": f"{year}"},
                {"Customer ID": 1002, "Company Name": "Beta Data Corp", "Segment": "Mid-Market", "Metric Value": 312500.00, "Period": f"{year}"},
                {"Customer ID": 1003, "Company Name": "Gamma Cloud Labs", "Segment": "Enterprise", "Metric Value": 289400.00, "Period": f"{year}"},
                {"Customer ID": 1004, "Company Name": "Delta AI Networks", "Segment": "Enterprise", "Metric Value": 245000.00, "Period": f"{year}"},
            ])
        elif "product" in p_lower or "item" in p_lower:
            primary_table = "products"
            select_cols = "p.product_id, p.product_name, p.category, p.unit_price"
            group_cols = "p.product_id, p.product_name, p.category, p.unit_price"
            sample_df = pd.DataFrame([
                {"Product ID": 201, "Product Name": "Cloud Gateway Pro", "Category": "Cloud", "Unit Price ($)": 399.00, "Quantity Sold": 1420},
                {"Product ID": 202, "Product Name": "DataVault Appliance", "Category": "Hardware", "Unit Price ($)": 790.00, "Quantity Sold": 890},
                {"Product ID": 203, "Product Name": "CyberShield Core", "Category": "Security", "Unit Price ($)": 450.00, "Quantity Sold": 1120},
                {"Product ID": 204, "Product Name": "Quantum Engine", "Category": "Software", "Unit Price ($)": 620.00, "Quantity Sold": 750},
            ])
        else:
            primary_table = "orders"
            select_cols = "o.order_id, o.shipping_region, o.status, o.total_amount"
            group_cols = "o.order_id, o.shipping_region, o.status, o.total_amount"
            sample_df = pd.DataFrame([
                {"Dimension / Entity": "Direct Transaction Volume", "Category": "Commercial Sales", "Calculated Metric ($)": 1425000.00, "Status": "Active"},
                {"Dimension / Entity": "Partner Channel Volume", "Category": "Reseller Network", "Calculated Metric ($)": 892000.00, "Status": "Active"},
                {"Dimension / Entity": "Online Enterprise Portal", "Category": "Digital Self-Serve", "Calculated Metric ($)": 674500.00, "Status": "Active"},
                {"Dimension / Entity": "Strategic Accounts RFP", "Category": "Direct Field Sales", "Calculated Metric ($)": 521000.00, "Status": "Active"},
            ])

        sql = f"""-- Dialect: {dialect}
-- Intent: Dynamic Query Synthesis for prompt: "{prompt[:60]}..."
SELECT 
    {select_cols},
    COUNT(*) AS record_frequency,
    ROUND(AVG(COALESCE(o.total_amount, 1000.0)), 2) AS estimated_avg
FROM {primary_table} {'c' if primary_table == 'customers' else 'p' if primary_table == 'products' else 'o'}
LEFT JOIN orders o ON 1=1
WHERE 1=1
GROUP BY {group_cols}
ORDER BY record_frequency DESC
LIMIT {limit};"""

        explanation = f"""### 📊 Natural Language Query Interpretation
Interpreted user inquiry: *"{prompt}"*. 

Synthesized an entity-mapped SQL projection across the **`{primary_table}`** and **`orders`** relational schemas. Relevant records matching the inferred business dimensions have been projected below.

---

### 🔍 Query Construction & Execution Logic
1. **Target Relation**: Inferred target entity `{primary_table}` based on keyword token distribution.
2. **Projection & Aggregation**: Selected entity keys, categorized metrics, and aggregated relative volume.
3. **Execution Safety**: Filtered with standard SQL bounds with safety limit `LIMIT {limit}`."""

        return {
            "sql": sql,
            "df": sample_df,
            "explanation": explanation,
            "suggested_followups": [
                "What were the top 10 products by revenue in 2025?",
                "Show monthly revenue trend for 2025",
                "Who are our top 5 customers by spend?"
            ]
        }

    def _handle_empty_query(self, dialect: str) -> NLtoSQLResult:
        empty_df = pd.DataFrame({"Status": ["No input query provided"], "Action": ["Please enter a business question or select an example query from the sidebar."]})
        return NLtoSQLResult(
            user_query="",
            intent="empty",
            explanation="Please provide a natural language question (e.g. *'What were the top 10 products by revenue in 2025?'*) to generate a SQL query and retrieve data.",
            sql_query="-- No query provided. Awaiting natural language prompt.",
            dataframe=empty_df,
            execution_time_ms=0.0,
            row_count=0,
            dialect=dialect
        )
