"""
tests/benchmarks.py
50 Enterprise NL-to-SQL Benchmark Questions Catalog & Schema Specifications
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

BENCHMARK_JSON_PATH = Path(__file__).parent / "benchmark_questions.json"


@dataclass
class BenchmarkQuestion:
    id: str
    tier: str
    question: str
    expected_tables: List[str]
    ground_truth_sql: str
    expected_chart_type: str
    verification_type: str  # 'query_execution', 'security_rejection', 'empty_result'

    @property
    def is_security_test(self) -> bool:
        return self.verification_type == "security_rejection"

    @property
    def is_empty_result_test(self) -> bool:
        return self.verification_type == "empty_result"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tier": self.tier,
            "question": self.question,
            "expected_tables": self.expected_tables,
            "ground_truth_sql": self.ground_truth_sql,
            "expected_chart_type": self.expected_chart_type,
            "verification_type": self.verification_type,
        }


def load_benchmarks(file_path: Optional[Path] = None) -> List[BenchmarkQuestion]:
    """Load benchmark questions from JSON catalog."""
    target_path = file_path or BENCHMARK_JSON_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Benchmark file not found at: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        BenchmarkQuestion(
            id=item["id"],
            tier=item["tier"],
            question=item["question"],
            expected_tables=item["expected_tables"],
            ground_truth_sql=item["ground_truth_sql"],
            expected_chart_type=item["expected_chart_type"],
            verification_type=item.get("verification_type", "query_execution"),
        )
        for item in data
    ]


def get_benchmarks_by_tier(tier_prefix: str) -> List[BenchmarkQuestion]:
    """Filter benchmark questions by tier prefix (e.g. 'Tier 1', 'Tier 2')."""
    all_bms = load_benchmarks()
    return [bm for bm in all_bms if bm.tier.startswith(tier_prefix)]


def get_tier_summary() -> Dict[str, int]:
    """Return count of benchmark questions per tier."""
    all_bms = load_benchmarks()
    counts = {}
    for bm in all_bms:
        counts[bm.tier] = counts.get(bm.tier, 0) + 1
    return counts


if __name__ == "__main__":
    bms = load_benchmarks()
    print(f"Loaded {len(bms)} benchmark questions across tiers:")
    for tier, count in get_tier_summary().items():
        print(f"  - {tier}: {count} queries")
