"""Tests for benchmark dataset integrity."""

import json
from pathlib import Path


def test_benchmark_file_structure():
    benchmark_path = Path("data/benchmark.json")
    assert benchmark_path.exists()
    with open(benchmark_path, "r") as f:
        data = json.load(f)

    assert len(data) >= 100
    categories = set()
    for item in data:
        assert "id" in item
        assert "category" in item
        assert "statements" in item
        assert "query" in item
        assert "is_consistent" in item
        assert len(item["statements"]) > 0
        assert len(item["query"]) == 2
        categories.add(item["category"])

    expected_categories = {
        "event ordering",
        "relative dates",
        "durations",
        "interval relations",
        "transitive inference",
        "inverse relations",
        "contradictions",
        "mixed temporal expressions",
    }
    assert expected_categories.issubset(categories)


def test_examples_file_structure():
    examples_path = Path("data/examples.json")
    assert examples_path.exists()
    with open(examples_path, "r") as f:
        data = json.load(f)

    assert len(data) >= 3
    for ex in data:
        assert "id" in ex
        assert "statements" in ex
        assert "query" in ex
