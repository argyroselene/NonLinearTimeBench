"""Tests for the ConsistencyChecker."""

from datetime import datetime
from temporal_reasoning.events import Event
from temporal_reasoning.relations import TemporalRelation
from temporal_reasoning.graph import TemporalGraph
from temporal_reasoning.consistency import ConsistencyChecker


def test_consistency_on_valid_graph():
    graph = TemporalGraph()
    graph.add_relation("A", "B", TemporalRelation.BEFORE)
    graph.add_relation("B", "C", TemporalRelation.BEFORE)

    checker = ConsistencyChecker()
    assert checker.is_consistent(graph)
    assert len(checker.check(graph)) == 0


def test_consistency_direct_mutual_conflict():
    graph = TemporalGraph()
    graph.add_relation("A", "B", TemporalRelation.BEFORE)
    graph.add_relation("B", "A", TemporalRelation.BEFORE)

    checker = ConsistencyChecker()
    assert not checker.is_consistent(graph)
    conflicts = checker.check(graph)
    assert any(c.conflict_type == "MUTUAL_BEFORE_CONFLICT" for c in conflicts)


def test_consistency_strict_order_cycle():
    # A -> B -> C -> A
    graph = TemporalGraph()
    graph.add_relation("A", "B", TemporalRelation.BEFORE)
    graph.add_relation("B", "C", TemporalRelation.BEFORE)
    graph.add_relation("C", "A", TemporalRelation.BEFORE)

    checker = ConsistencyChecker()
    assert not checker.is_consistent(graph)
    conflicts = checker.check(graph)
    assert any(c.conflict_type == "STRICT_ORDER_CYCLE" for c in conflicts)


def test_consistency_disjoint_relation_conflict():
    graph = TemporalGraph()
    graph.add_relation("A", "B", TemporalRelation.BEFORE)
    graph.add_relation("A", "B", TemporalRelation.AFTER)

    checker = ConsistencyChecker()
    assert not checker.is_consistent(graph)
    conflicts = checker.check(graph)
    assert any(c.conflict_type == "DISJOINT_RELATIONS" for c in conflicts)
