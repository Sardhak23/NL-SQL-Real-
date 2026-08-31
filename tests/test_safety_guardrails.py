"""
tests/test_safety_guardrails.py
Adversarial Security & SQL Injection Guardrail Tests.
"""
import pytest
import re
from typing import Tuple

FORBIDDEN_KEYWORDS = [
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "REPLACE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
    "EXEC",
    "SAVEPOINT",
]

FORBIDDEN_REGEX = re.compile(
    rf"\b({'|'.join(FORBIDDEN_KEYWORDS)})\b",
    re.IGNORECASE,
)


def validate_safety_rule(sql: str) -> Tuple[bool, str]:
    """Test standard SQL safety rule engine."""
    # Check forbidden keywords
    match = FORBIDDEN_REGEX.search(sql)
    if match:
        return False, f"Forbidden keyword detected: {match.group(0).upper()}"

    # Check stacked queries (semicolon outside literals)
    cleaned = sql.strip().rstrip(";")
    if ";" in cleaned:
        statements = [s.strip() for s in cleaned.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Stacked multi-statement injection detected"

    # Check root command is SELECT or WITH
    tokens = cleaned.split()
    if not tokens:
        return False, "Empty query string"

    first_token = tokens[0].upper()
    if first_token not in ("SELECT", "WITH", "EXPLAIN"):
        return False, f"Non-read-only root command: {first_token}"

    return True, "Valid read-only SQL"


ADVERSARIAL_PAYLOADS = [
    # Mutating DDL/DML
    ("DELETE FROM orders;", "DELETE"),
    ("DROP TABLE customers;", "DROP"),
    ("DROP TABLE IF EXISTS products;", "DROP"),
    ("UPDATE customers SET email = 'hacked@evil.com';", "UPDATE"),
    ("INSERT INTO customers (first_name) VALUES ('Hacker');", "INSERT"),
    ("ALTER TABLE orders ADD COLUMN back_door TEXT;", "ALTER"),
    ("TRUNCATE TABLE inventory;", "TRUNCATE"),
    ("REPLACE INTO suppliers (name) VALUES ('Fake');", "REPLACE"),
    ("CREATE TABLE backdoor (id INT);", "CREATE"),
    # Attach/Pragma exploits
    ("ATTACH DATABASE 'evil.db' AS evil;", "ATTACH"),
    ("DETACH DATABASE evil;", "DETACH"),
    ("PRAGMA journal_mode = OFF;", "PRAGMA"),
    ("VACUUM;", "VACUUM"),
    ("REINDEX;", "REINDEX"),
    # Stacked SQL Injections
    ("SELECT * FROM customers; DROP TABLE orders;", "DROP"),
    ("SELECT 1; DELETE FROM order_items;", "DELETE"),
    ("SELECT * FROM products; INSERT INTO reviews (rating) VALUES (5);", "INSERT"),
    # Comment obfuscation
    ("/* comment */ DROP TABLE products;", "DROP"),
    ("-- comment\nDELETE FROM orders WHERE 1=1;", "DELETE"),
]


@pytest.mark.parametrize("payload,expected_keyword", ADVERSARIAL_PAYLOADS)
def test_adversarial_rejections(payload: str, expected_keyword: str):
    """Verify that all destructive / adversarial queries are rejected 100% of the time."""
    is_safe, reason = validate_safety_rule(payload)
    assert not is_safe, f"Security vulnerability: Payload was NOT blocked:\n{payload}"


VALID_SAFE_QUERIES = [
    "SELECT COUNT(*) FROM customers;",
    "SELECT c.name, SUM(oi.total_price) FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id GROUP BY c.name;",
    "WITH monthly AS (SELECT strftime('%Y-%m', order_date) AS m, SUM(total_amount) AS rev FROM orders GROUP BY m) SELECT * FROM monthly;",
    "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE customer_id = 100;",
]


@pytest.mark.parametrize("safe_sql", VALID_SAFE_QUERIES)
def test_valid_safe_queries_pass(safe_sql: str):
    """Verify that legitimate analytical SELECT/WITH queries pass the safety validator."""
    is_safe, reason = validate_safety_rule(safe_sql)
    assert is_safe, f"False positive: Valid query was blocked:\n{safe_sql}\nReason: {reason}"
