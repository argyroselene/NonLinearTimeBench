"""Tests for the TemporalGraph data structure."""

from temporal_reasoning.events import Event
from temporal_reasoning.relations import TemporalRelation
from temporal_reasoning.graph import TemporalGraph


def test_graph_add_event_and_lookup():
    graph = TemporalGraph()
    e1 = Event(event_id="E1", description="Alice arrived")
    graph.add_event(e1)

    assert graph.get_event("E1") == e1
    assert graph.get_event("Alice arrived") == e1
    assert graph.get_event("NonExistent") is None


def test_graph_add_relation_and_query():
    graph = TemporalGraph()
    e1 = Event(event_id="E1", description="Alice arrived")
    e2 = Event(event_id="E2", description="Bob arrived")
    graph.add_event(e1)
    graph.add_event(e2)

    graph.add_relation(e1, e2, TemporalRelation.BEFORE)
    assert graph.get_relation(e1, e2) == TemporalRelation.BEFORE
    assert graph.get_relation(e2, e1) is None
    assert graph.get_relations_between(e1, e2) == {TemporalRelation.BEFORE}


def test_graph_find_path():
    graph = TemporalGraph()
    e1 = Event(event_id="E1", description="Event 1")
    e2 = Event(event_id="E2", description="Event 2")
    e3 = Event(event_id="E3", description="Event 3")

    graph.add_relation(e1, e2, TemporalRelation.BEFORE)
    graph.add_relation(e2, e3, TemporalRelation.BEFORE)

    path = graph.find_path("E1", "E3")
    assert path is not None
    assert len(path) == 2
    assert path[0].source_id == "E1" and path[0].target_id == "E2"
    assert path[1].source_id == "E2" and path[1].target_id == "E3"


def test_graph_export_dot_and_dict():
    graph = TemporalGraph()
    e1 = Event(event_id="E1", description="Start")
    e2 = Event(event_id="E2", description="Finish")
    graph.add_relation(e1, e2, TemporalRelation.BEFORE)

    dot = graph.to_dot()
    assert "digraph TemporalGraph" in dot
    assert '"E1" -> "E2"' in dot

    data = graph.to_dict()
    assert len(data["events"]) == 2
    assert len(data["edges"]) == 1
