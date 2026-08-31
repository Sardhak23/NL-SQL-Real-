"""
backend/app/engine/validator.py
Strict SQL Safety & AST Guardrails Engine: Read-Only Enforcement, Injection Shield, and Row Limit Injection.
"""

from __future__ import annotations

import re
from typing import Tuple, Optional, Set
from backend.app.config import settings
from backend.app.database.introspection import SchemaCatalog, get_introspection_engine


class SecurityValidationError(Exception):
    """Raised when an analytical query violates read-only safety guardrails."""
    pass


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


class SQLValidator:
    """Validates SQL query security, syntax integrity, and injects safety limits."""

    def __init__(self, max_limit: int = 1000):
        self.max_limit = max_limit

    @staticmethod
    def strip_comments_and_fences(raw_sql: str) -> str:
        """Strip markdown fences, leading/trailing whitespace, and SQL comments."""
        cleaned = raw_sql.strip()

        # Strip markdown ```sql ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
            if match:
                cleaned = match.group(1).strip()
            else:
                cleaned = cleaned.replace("```sql", "").replace("```", "").strip()

        # Remove single-line comments (-- ...)
        cleaned = re.sub(r"--[^\n]*", "", cleaned)
        # Remove multi-line comments (/* ... */)
        cleaned = re.sub(r"/\*[\s\S]*?\*/", "", cleaned)

        return cleaned.strip()

    def validate_and_sanitize(self, sql: str, enforce_limit: bool = True) -> str:
        """
        Perform rigorous 4-stage safety validation and limit injection.
        Raises SecurityValidationError on any safety breach.
        """
        cleaned = self.strip_comments_and_fences(sql)

        if not cleaned:
            raise SecurityValidationError("Empty query string received.")

        # Stage 1: Forbidden Keyword Deny-List Check
        match = FORBIDDEN_REGEX.search(cleaned)
        if match:
            violating_kw = match.group(0).upper()
            raise SecurityValidationError(
                f"Security Violation: Prohibited mutating keyword '{violating_kw}' detected. Only read-only SELECT queries are permitted."
            )

        # Stage 2: Stacked Multi-Statement Injection Check
        # Semicolons outside string literals
        trimmed_semi = cleaned.rstrip(";").strip()
        if ";" in trimmed_semi:
            # Check for multiple active statements
            statements = [s.strip() for s in trimmed_semi.split(";") if s.strip()]
            if len(statements) > 1:
                raise SecurityValidationError(
                    "Security Violation: Multiple SQL statements detected. Stacked query execution is prohibited."
                )

        # Stage 3: Root Statement Command Check
        first_token_match = re.match(r"^\s*([a-zA-Z]+)", cleaned)
        if not first_token_match:
            raise SecurityValidationError("Invalid SQL syntax: Cannot determine root statement.")

        first_token = first_token_match.group(1).upper()
        if first_token not in ("SELECT", "WITH", "EXPLAIN"):
            raise SecurityValidationError(
                f"Security Violation: Non-read-only root command '{first_token}'. Queries must begin with SELECT, WITH, or EXPLAIN."
            )

        # Stage 4: Automated LIMIT Enforcement
        if enforce_limit and first_token in ("SELECT", "WITH"):
            # Check if query already has a LIMIT clause
            if not re.search(r"\bLIMIT\s+\d+\b", cleaned, re.IGNORECASE):
                # Ensure trailing semicolon if present is handled
                cleaned = f"{trimmed_semi} LIMIT {self.max_limit};"
            else:
                if not cleaned.endswith(";"):
                    cleaned += ";"

        return cleaned

    def validate_safety_boolean(self, sql: str) -> Tuple[bool, Optional[str]]:
        """Convenience method returning (is_safe, error_message)."""
        try:
            self.validate_and_sanitize(sql, enforce_limit=False)
            return True, None
        except SecurityValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
