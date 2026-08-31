"""
tests/test_benchmark_50.py
Pytest Suite for 50 Enterprise NL-to-SQL Benchmark Questions.
"""
import pytest
import sqlite3
import re
from pathlib import Path
from tests.benchmarks import load_benchmarks, BenchmarkQuestion

WORKSPACE_ROOT = Path(__file__).parent.parent
DB_CANDIDATES = [
    WORKSPACE_ROOT / "ecommerce.db",
    WORKSPACE_ROOT / "data" / "ecommerce.db",
    Path("C:/Users/A SAI SARDHAK/.gemini/antigravity/scratch/nl_to_sql_ui/ecommerce.db"),
]

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|REPLACE|CREATE|GRANT|REVOKE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|EXEC|SAVEPOINT)\b",
    re.IGNORECASE,
)


@pytest.fixture(scope="session")
def db_path() -> Path:
    """Fixture providing the active SQLite database path."""
    for cand in DB_CANDIDATES:
        if cand.exists() and cand.stat().st_size > 0:
            return cand
    pytest.skip("ecommerce.db not found. Generate it first using scripts/generate_dataset.py.")


ALL_BENCHMARKS = load_benchmarks()


@pytest.mark.parametrize("bm", ALL_BENCHMARKS, ids=[bm.id for bm in ALL_BENCHMARKS])
def test_enterprise_benchmark_question(bm: BenchmarkQuestion, db_path: Path):
    """Test each of the 50 enterprise benchmark questions."""
    # 1. Verify Structure & Metadata
    assert bm.id.startswith("BM_"), f"Invalid ID format: {bm.id}"
    assert len(bm.question) > 5, "Question string too short"
    assert len(bm.expected_tables) >= 1, "Must declare at least 1 expected table"
    assert bm.expected_chart_type in (
        "metric",
        "bar",
        "horizontal_bar",
        "line",
        "area",
        "donut",
        "scatter",
        "table",
        "none",
    ), f"Invalid chart type: {bm.expected_chart_type}"

    # 2. Security Rejection Test
    if bm.is_security_test:
        match = FORBIDDEN_KEYWORDS.search(bm.ground_truth_sql)
        has_multi = ";" in bm.ground_truth_sql.strip().rstrip(";")
        is_blocked = (match is not None) or has_multi
        assert is_blocked, f"Adversarial security query {bm.id} was not flagged as dangerous!"
        return

    # 3. Read-Only Validation
    assert not FORBIDDEN_KEYWORDS.search(
        bm.ground_truth_sql
    ), f"Non-security query {bm.id} contains forbidden mutating keywords!"

    # 4. SQLite Execution
    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(bm.ground_truth_sql)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description] if cursor.description else []

        assert len(col_names) > 0, f"Query {bm.id} returned no columns"

        # 5. Empty Result Verification
        if bm.is_empty_result_test:
            assert len(rows) == 0, f"Empty-result test {bm.id} returned {len(rows)} rows unexpectedly"
        else:
            # Query returned without exception; non-empty or empty is valid depending on query
            pass

    except sqlite3.OperationalError as e:
        pytest.fail(f"OperationalError executing {bm.id}: {e}\nSQL: {bm.ground_truth_sql}")
    except sqlite3.DatabaseError as e:
        pytest.fail(f"DatabaseError executing {bm.id}: {e}\nSQL: {bm.ground_truth_sql}")
    finally:
        conn.close()
