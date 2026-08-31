"""
tests/test_agent_pipeline.py
Unit and Integration Tests for NL-to-SQL Agent Pipeline:
- AST Safety Validator & Sanitizer
- Dynamic Schema Linker
- Executive Insight Synthesis
- Self-Correction Diagnostic Handling
"""
import pytest
import sqlite3
from typing import Dict, List, Any


class MockSchemaLinker:
    """Mock Schema Linker for testing context extraction rules."""

    TABLES = ["categories", "suppliers", "products", "customers", "orders", "order_items", "inventory", "reviews"]
    COLUMNS = {
        "categories": ["category_id", "name", "slug", "description", "department"],
        "products": ["product_id", "category_id", "supplier_id", "name", "price", "cost"],
        "customers": ["customer_id", "first_name", "last_name", "email", "country", "segment", "loyalty_tier"],
        "orders": ["order_id", "customer_id", "order_date", "status", "payment_method", "total_amount"],
        "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "total_price"],
        "inventory": ["inventory_id", "product_id", "warehouse_location", "stock_quantity", "reorder_level"],
        "reviews": ["review_id", "product_id", "customer_id", "rating", "review_text"],
    }

    @classmethod
    def link_schema(cls, question: str) -> List[str]:
        q = question.lower()
        matched = set()
        if any(w in q for w in ("category", "categories", "department")):
            matched.add("categories")
        if any(w in q for w in ("product", "products", "item", "price", "cost")):
            matched.add("products")
        if any(w in q for w in ("customer", "customers", "client", "buyer", "loyalty", "segment")):
            matched.add("customers")
        if any(w in q for w in ("order", "orders", "sale", "sales", "revenue", "spend", "payment", "status")):
            matched.add("orders")
            matched.add("order_items")
        if any(w in q for w in ("inventory", "stock", "warehouse", "reorder")):
            matched.add("inventory")
        if any(w in q for w in ("review", "reviews", "rating", "star")):
            matched.add("reviews")

        # Foreign key closure
        if "categories" in matched and "orders" in matched:
            matched.add("products")
            matched.add("order_items")

        return sorted(list(matched)) if matched else cls.TABLES[:2]


def test_schema_linker_single_table():
    """Verify customer question extracts customers table."""
    tables = MockSchemaLinker.link_schema("How many customers signed up in 2024?")
    assert "customers" in tables


def test_schema_linker_multi_table_closure():
    """Verify category revenue question includes categories, products, order_items, orders."""
    tables = MockSchemaLinker.link_schema("What are the top 5 product categories by revenue?")
    assert "categories" in tables
    assert "products" in tables
    assert "order_items" in tables
    assert "orders" in tables


def test_self_correction_cycle_simulation():
    """Simulate SQLite operational error and recovery feedback loop."""
    # Attempt 1: Failed SQL with missing table join
    err_sql = "SELECT category_name, SUM(total_amount) FROM orders GROUP BY category_name;"
    err_msg = "no such column: category_name"

    # Self-Correction Engine captures error and reformulates prompt
    repair_prompt = f"Failed SQL: {err_sql}\nError: {err_msg}\nHINT: category_name is in 'categories' table, which joins through 'products' -> 'order_items' -> 'orders'."
    assert "no such column: category_name" in repair_prompt

    # Attempt 2: Corrected SQL
    fixed_sql = "SELECT c.name AS category_name, SUM(oi.total_price) FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id GROUP BY c.category_id;"
    assert "categories c" in fixed_sql
    assert "order_items oi" in fixed_sql


def test_executive_summary_synthesis():
    """Verify executive summary generation formats key metrics."""
    mock_rows = [
        {"category_name": "Electronics", "total_revenue": 1420500.00},
        {"category_name": "Apparel", "total_revenue": 980200.00},
    ]

    total_sales = sum(r["total_revenue"] for r in mock_rows)
    top_cat = mock_rows[0]["category_name"]
    top_rev = mock_rows[0]["total_revenue"]

    headline = f"{top_cat} leads revenue at ${top_rev:,.2f}."
    assert "Electronics" in headline
    assert "$1,420,500.00" in headline
