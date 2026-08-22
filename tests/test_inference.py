"""Tests for symbolic temporal inference."""

from temporal_reasoning.events import Event
from temporal_reasoning.relations import TemporalRelation
from temporal_reasoning.graph import TemporalGraph
from temporal_reasoning.inference import InferenceEngine


def test_inverse_inference():
    graph = TemporalGraph()
    e1 = Event(event_id="E1", description="Alice arrived")
    e2 = Event(event_id="E2", description="Bob arrived")
    graph.add_relation(e1, e2, TemporalRelation.BEFORE)

    engine = InferenceEngine(enable_inverse=True)
    res = engine.run(graph)

    assert res.edges_added == 1
    assert graph.get_relation(e2, e1) == TemporalRelation.AFTER
    edge = [e for e in graph.get_all_edges() if e.source_id == "E2" and e.target_id == "E1"][0]
    assert edge.is_inferred is True
    assert "Inverse of" in edge.provenance


def test_inverse_during_contains():
    graph = TemporalGraph()
    e1 = Event(event_id="E1", description="Lecture")
    e2 = Event(event_id="E2", description="Semester")
    graph.add_relation(e1, e2, TemporalRelation.DURING)

    engine = InferenceEngine(enable_inverse=True)
    engine.run(graph)

    assert graph.get_relation(e2, e1) == TemporalRelation.CONTAINS


def test_transitivity_before_chain():
    # Alice BEFORE Bob, Bob BEFORE Charlie => Alice BEFORE Charlie, Charlie AFTER Alice
    graph = TemporalGraph()
    e1 = Event(event_id="E1", description="Alice")
    e2 = Event(event_id="E2", description="Bob")
    e3 = Event(event_id="E3", description="Charlie")

    graph.add_relation(e1, e2, TemporalRelation.BEFORE)
    graph.add_relation(e2, e3, TemporalRelation.BEFORE)

    engine = InferenceEngine(enable_inverse=True, enable_transitivity=True)
    res = engine.run(graph)

    assert graph.get_relation("E1", "E3") == TemporalRelation.BEFORE
    assert graph.get_relation("E3", "E1") == TemporalRelation.AFTER


def test_transitivity_with_equality():
    # A EQUAL B, B BEFORE C => A BEFORE C
    graph = TemporalGraph()
    graph.add_relation("A", "B", TemporalRelation.EQUAL)
    graph.add_relation("B", "C", TemporalRelation.BEFORE)

    engine = InferenceEngine(enable_inverse=True, enable_transitivity=True)
    engine.run(graph)

    assert graph.get_relation("A", "C") == TemporalRelation.BEFORE


def test_interval_bound_completion_and_deduction():
    # Meeting starts at 10:00, duration 90 minutes => infer ends at 11:30
    # Lunch starts at 12:00, ends at 13:00 => infer Meeting BEFORE Lunch
    from datetime import datetime, timedelta
    graph = TemporalGraph()
    e1 = Event(
        event_id="E1",
        description="Meeting",
        start_time=datetime(2026, 8, 22, 10, 0, 0),
        duration=timedelta(minutes=90),
    )
    e2 = Event(
        event_id="E2",
        description="Lunch",
        start_time=datetime(2026, 8, 22, 12, 0, 0),
        end_time=datetime(2026, 8, 22, 13, 0, 0),
    )
    graph.add_event(e1)
    graph.add_event(e2)

    engine = InferenceEngine(enable_interval=True, enable_inverse=True)
    engine.run(graph)

    assert e1.end_time == datetime(2026, 8, 22, 11, 30, 0)
    assert graph.get_relation("E1", "E2") == TemporalRelation.BEFORE
    assert graph.get_relation("E2", "E1") == TemporalRelation.AFTER


