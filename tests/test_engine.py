"""Tests for the high-level TemporalReasoningEngine."""

from temporal_reasoning import TemporalReasoningEngine, TemporalRelation


def test_engine_basic_reasoning_pipeline():
    engine = TemporalReasoningEngine()
    engine.add_statement("Alice arrived before Bob.")
    engine.add_statement("Bob left before Charlie.")

    result = engine.query("Alice", "Charlie")
    assert result == TemporalRelation.BEFORE

    inv_result = engine.query("Charlie", "Alice")
    assert inv_result == TemporalRelation.AFTER

    explanation = engine.query_explanation("Alice", "Charlie")
    assert explanation is not None
    assert "Transitivity" in explanation


def test_engine_consistency_integration():
    engine = TemporalReasoningEngine()
    engine.add_statement("Event A before Event B.")
    engine.add_statement("Event B before Event A.")

    assert not engine.is_consistent()
    conflicts = engine.check_consistency()
    assert len(conflicts) > 0


def test_engine_reset():
    engine = TemporalReasoningEngine()
    engine.add_statement("Event 1 before Event 2.")
    assert engine.query("Event 1", "Event 2") == TemporalRelation.BEFORE

    engine.reset()
    assert engine.query("Event 1", "Event 2") is None
