"""
backend/verify_backend.py
Comprehensive End-to-End Verification Suite for Backend, Dataset, and AI Engine.
"""

from __future__ import annotations

import sys
import os
import time
import json
import sqlite3
from pathlib import Path

# Add project root to sys.path
WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.app.config import settings
from backend.app.database.introspection import IntrospectionEngine, get_introspection_engine
from backend.app.engine.schema_linker import SchemaLinker
from backend.app.engine.validator import SQLValidator, SecurityValidationError
from backend.app.engine.executor import SQLExecutor
from backend.app.engine.insights import InsightEngine, determine_chart_archetype
from backend.app.engine.provider import DeterministicFallbackProvider, get_llm_provider
from backend.app.engine.self_correction import SelfCorrectionEngine
from backend.app.models.schemas import ChatRequest, QueryRequest, ExecuteRequest
from backend.app.api.health import get_health_status
from backend.app.api.schema import get_database_schema, refresh_database_schema
from backend.app.api.chat import handle_chat_query, handle_direct_execute
from backend.app.api.insights import generate_insights, InsightsRequest
from backend.app.api.benchmarks import get_benchmarks


def run_full_verification():
    print("=" * 80)
    print("NL-SQL COPILOT BACKEND & DATABASE VERIFICATION SUITE")
    print(f"Workspace: {WORKSPACE_ROOT}")
    print(f"Database : {settings.db_path}")
    print("=" * 80)

    passed_checks = 0
    total_checks = 0

    def check(name: str, condition: bool, extra: str = ""):
        nonlocal passed_checks, total_checks
        total_checks += 1
        status = "PASS" if condition else "FAIL"
        if condition:
            passed_checks += 1
            print(f"  [PASS] {name} {extra}")
        else:
            print(f"  [FAIL] {name} {extra}")

    # =========================================================================
    # Test 1: Database Existence & Schema Verification
    # =========================================================================
    print("\n--- Test Suite 1: Database & Introspection ---")
    db_file = Path(settings.db_path).resolve()
    if not db_file.exists():
        print(f"Database {db_file} not found. Running dataset generator...")
        import scripts.generate_dataset as gen
        gen.main()
        settings.refresh_db_path()

    check("Database File Exists", db_file.exists(), f"({db_file.name}, size: {db_file.stat().st_size / (1024*1024):.1f} MB)")

    engine = get_introspection_engine()
    catalog = engine.refresh()

    check("Catalog Introspected >= 8 Tables", catalog.total_tables >= 8, f"({catalog.total_tables} tables found)")
    
    expected_tables = ["categories", "suppliers", "products", "customers", "orders", "order_items", "inventory", "reviews"]
    for tbl in expected_tables:
        check(f"Table '{tbl}' Present in Catalog", tbl in catalog.tables, f"({catalog.tables.get(tbl, None).row_count if tbl in catalog.tables else 0:,} rows)")

    orders_count = catalog.tables["orders"].row_count if "orders" in catalog.tables else 0
    check("Orders Scale >= 500,000", orders_count >= 500000, f"({orders_count:,} orders)")

    order_items_count = catalog.tables["order_items"].row_count if "order_items" in catalog.tables else 0
    check("Order Items Scale >= 1,000,000", order_items_count >= 1000000, f"({order_items_count:,} items)")

    # =========================================================================
    # Test 2: Schema Linker & Graph Relational Closure
    # =========================================================================
    print("\n--- Test Suite 2: Schema Linking & Relational Graph Closure ---")
    linker = SchemaLinker(catalog)
    
    # Query involving categories and orders (should bridge via products and order_items)
    linked_tbls, ddl = linker.link_schema("What are the top product categories by sales revenue in 2024?")
    check("Linker Identified 'categories'", "categories" in linked_tbls)
    check("Linker Identified 'orders'", "orders" in linked_tbls)
    check("Linker Graph Closure Added 'products' & 'order_items'", "products" in linked_tbls and "order_items" in linked_tbls, f"(Linked: {linked_tbls})")
    check("Formatted Schema DDL Non-Empty", len(ddl) > 100)

    # =========================================================================
    # Test 3: SQL Safety Validator & Guardrails
    # =========================================================================
    print("\n--- Test Suite 3: SQL Safety Validator ---")
    validator = SQLValidator(max_limit=1000)

    # Valid SELECT
    safe_sql = "SELECT c.name, SUM(oi.total_price) FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id GROUP BY c.name"
    sanitized = validator.validate_and_sanitize(safe_sql, enforce_limit=True)
    check("Valid SELECT passes and gets LIMIT appended", "LIMIT 1000" in sanitized)

    # Adversarial queries
    adversarial_tests = [
        "DROP TABLE customers;",
        "DELETE FROM orders WHERE status = 'cancelled';",
        "UPDATE customers SET loyalty_tier = 'Gold';",
        "INSERT INTO products (name) VALUES ('Hacked');",
        "SELECT * FROM customers; DROP TABLE orders;",
        "ATTACH DATABASE 'evil.db' AS evil;",
        "PRAGMA journal_mode = OFF;",
    ]
    for adv in adversarial_tests:
        try:
            validator.validate_and_sanitize(adv)
            check(f"Blocked Adversarial: '{adv}'", False, "FAILED TO BLOCK!")
        except SecurityValidationError:
            check(f"Blocked Adversarial: '{adv}'", True)

    # =========================================================================
    # Test 4: Chart Advisor Heuristics
    # =========================================================================
    print("\n--- Test Suite 4: Chart Advisor Heuristics ---")
    c_metric = determine_chart_archetype(["total_revenue"], {"total_revenue": "float"}, 1)
    check("Rule 1: 1x1 Numeric -> Metric Card", c_metric == "metric")

    c_bar = determine_chart_archetype(["category_name", "total_revenue"], {"category_name": "text", "total_revenue": "float"}, 5, {"category_name": 5})
    check("Rule 2: Categorical Ranking -> Bar Chart", c_bar == "bar")

    c_donut = determine_chart_archetype(["status", "order_count"], {"status": "text", "order_count": "int"}, 5, {"status": 5})
    check("Rule 3: Low Cardinality Share -> Donut Chart", c_donut == "donut")

    c_line = determine_chart_archetype(["month", "monthly_revenue", "order_count"], {"month": "text", "monthly_revenue": "float", "order_count": "int"}, 12)
    check("Rule 4: Monthly Trend -> Line Chart", c_line == "line")

    c_area = determine_chart_archetype(["month", "cumulative_revenue"], {"month": "text", "cumulative_revenue": "float"}, 12)
    check("Rule 5: Cumulative Series -> Area Chart", c_area == "area")

    c_table = determine_chart_archetype(["id", "first_name", "last_name", "email", "city", "signup_date"], {"id": "int"}, 50)
    check("Rule 6: Multi-Attribute Record Set -> Table View", c_table == "table")

    # =========================================================================
    # Test 5: End-to-End Pipeline & Self-Correction
    # =========================================================================
    print("\n--- Test Suite 5: End-to-End Self-Correction Pipeline ---")
    sc_engine = SelfCorrectionEngine(max_retries=3)

    resp1 = sc_engine.process_query("What are the top 5 product categories by total sales revenue in 2024?")
    check("E2E Query 1 Execution Success", resp1.success, f"({resp1.row_count} rows in {resp1.execution_time_ms}ms)")
    check("E2E Query 1 Has Executive Headline", bool(resp1.executive_summary and resp1.executive_summary.headline))
    check("E2E Query 1 Chart Spec Is Bar", resp1.chart_spec.chart_type == "bar")

    resp2 = sc_engine.process_query("What is the monthly sales revenue trend for completed orders in 2024?")
    check("E2E Query 2 Execution Success", resp2.success, f"({resp2.row_count} rows in {resp2.execution_time_ms}ms)")
    check("E2E Query 2 Chart Spec Is Line", resp2.chart_spec.chart_type == "line")

    resp3 = sc_engine.process_query("How many total customers are in the database?")
    check("E2E Query 3 Execution Success", resp3.success, f"({resp3.row_count} rows in {resp3.execution_time_ms}ms)")
    check("E2E Query 3 Chart Spec Is Metric", resp3.chart_spec.chart_type == "metric")

    # Adversarial query through pipeline
    resp_adv = sc_engine.process_query("Delete all cancelled orders from the orders table.")
    check("Adversarial Query Gracefully Rejected", not resp_adv.success and resp_adv.error_type == "security_violation")

    # =========================================================================
    # Test 6: FastAPI API Endpoints
    # =========================================================================
    print("\n--- Test Suite 6: API Endpoints ---")
    health = get_health_status()
    check("GET /api/health Returns Healthy", health.status == "healthy" and health.database_connected)

    schema_res = get_database_schema()
    check("GET /api/schema Returns SchemaResponse", schema_res.total_tables >= 8 and len(schema_res.tables) >= 8)

    chat_req = ChatRequest(question="What are the top 5 product categories by revenue in 2024?")
    chat_res = handle_chat_query(chat_req)
    check("POST /api/chat Returns Structured Response", chat_res.success and chat_res.row_count > 0)

    exec_req = ExecuteRequest(sql="SELECT status, COUNT(*) AS count FROM orders GROUP BY status;")
    exec_res = handle_direct_execute(exec_req)
    check("POST /api/execute Runs Valid Read-Only Query", exec_res.success and exec_res.row_count > 0)

    bms = get_benchmarks()
    check("GET /api/benchmarks Returns Curated Questions", len(bms) == 50)

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print(f"VERIFICATION SUMMARY: {passed_checks}/{total_checks} CHECKS PASSED ({(passed_checks/total_checks)*100:.1f}%)")
    print("=" * 80)

    return passed_checks == total_checks


if __name__ == "__main__":
    success = run_full_verification()
    sys.exit(0 if success else 1)
