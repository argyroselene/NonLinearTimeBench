"""Tests for the BenchmarkEvaluator framework."""

from pathlib import Path
from temporal_reasoning.evaluator import BenchmarkEvaluator, EvaluationMetrics


def test_evaluator_on_synthetic_data():
    evaluator = BenchmarkEvaluator()
    sample_data = [
        {
            "id": "t1",
            "category": "transitivity",
            "statements": ["A before B.", "B before C."],
            "query": ["A", "C"],
            "expected": "before",
            "is_consistent": True,
        },
        {
            "id": "t2",
            "category": "inverse",
            "statements": ["X during Y."],
            "query": ["Y", "X"],
            "expected": "contains",
            "is_consistent": True,
        },
        {
            "id": "t3",
            "category": "contradiction",
            "statements": ["M before N.", "N before M."],
            "query": ["M", "N"],
            "expected": None,
            "is_consistent": False,
        },
    ]

    metrics = evaluator.evaluate_dataset(sample_data)
    assert metrics.total_examples == 3
    assert metrics.correct_predictions == 3
    assert metrics.accuracy == 1.0
    assert metrics.consistency_rate == 1.0
    assert metrics.f1_macro > 0.9

    report = metrics.summary_report()
    assert "Temporal Reasoning Evaluation" in report
    assert "Overall Accuracy" in report


def test_evaluator_file_run():
    evaluator = BenchmarkEvaluator()
    metrics = evaluator.evaluate_file("data/examples.json")
    assert metrics.total_examples == 3
    assert metrics.accuracy == 1.0
