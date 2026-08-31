"""
backend/app/api/benchmarks.py
Curated 50 Enterprise Benchmark Questions Endpoint.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter

WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
BENCHMARK_JSON_PATH = WORKSPACE_ROOT / "tests" / "benchmark_questions.json"

router = APIRouter()


@router.get("/benchmarks", response_model=List[Dict[str, Any]])
def get_benchmarks() -> List[Dict[str, Any]]:
    """Retrieve 50 enterprise benchmark questions categorized by analytical tiers."""
    if not BENCHMARK_JSON_PATH.exists():
        return []

    try:
        with open(BENCHMARK_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return []
