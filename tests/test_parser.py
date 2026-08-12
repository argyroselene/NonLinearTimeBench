"""Tests for natural-language statement parser."""

from datetime import datetime, timedelta
from temporal_reasoning.parser import StatementParser
from temporal_reasoning.relations import TemporalRelation


def test_parse_simple_before_relation():
    parser = StatementParser()
    stmt = parser.parse_sentence("Alice arrived before Bob.")
    assert stmt.statement_type == "RELATION"
    assert stmt.relation == TemporalRelation.BEFORE
    assert stmt.source_event.description.lower() == "alice"
    assert stmt.target_event.description.lower() == "bob"


def test_parse_after_relation():
    parser = StatementParser()
    stmt = parser.parse_sentence("Bob left after Alice.")
    assert stmt.statement_type == "RELATION"
    assert stmt.relation == TemporalRelation.AFTER
    assert stmt.source_event.description.lower() == "bob"
    assert stmt.target_event.description.lower() == "alice"


def test_parse_during_relation():
    parser = StatementParser()
    stmt = parser.parse_sentence("Presentation during Workshop.")
    assert stmt.statement_type == "RELATION"
    assert stmt.relation == TemporalRelation.DURING


def test_parse_event_start_and_duration_coreference():
    anchor = datetime(2026, 8, 12, 0, 0, 0)
    parser = StatementParser(anchor_date=anchor)
    statements = parser.parse("The meeting started at 10:00. It lasted for 90 minutes.")
    assert len(statements) == 2

    s1 = statements[0]
    assert s1.statement_type == "EVENT_BOUND"
    assert s1.bound_type == "start"
    assert s1.bound_value == datetime(2026, 8, 12, 10, 0, 0)
    ev = s1.source_event

    s2 = statements[1]
    assert s2.statement_type == "EVENT_BOUND"
    assert s2.bound_type == "duration"
    assert s2.bound_value == timedelta(minutes=90)
    # Coreference check: the event modified by sentence 2 must be the meeting from sentence 1
    assert s2.source_event == ev
    assert ev.start_time == datetime(2026, 8, 12, 10, 0, 0)
    assert ev.duration == timedelta(minutes=90)


def test_parse_equal_relation():
    parser = StatementParser()
    stmt = parser.parse_sentence("Task A happened at the same time as Task B.")
    assert stmt.statement_type == "RELATION"
    assert stmt.relation == TemporalRelation.EQUAL
