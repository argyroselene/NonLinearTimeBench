"""Robustness, edge-case, and malformed input test suite."""

import pytest
from datetime import datetime, timedelta
from temporal_reasoning import (
    TemporalReasoningEngine,
    TemporalRelation,
    Event,
    StatementParser,
    extract_temporal_expressions,
    normalize_text,
)


def test_empty_input_statement():
    engine = TemporalReasoningEngine()
    parsed = engine.add_statement("")
    assert len(parsed) == 0
    assert engine.query("Nobody", "Ghost") is None


def test_whitespace_and_punctuation_input():
    engine = TemporalReasoningEngine()
    parsed = engine.add_statement("   ... ;;; \n\n  ")
    assert len(parsed) == 0


def test_malformed_unparseable_sentence():
    engine = TemporalReasoningEngine()
    # Random non-temporal sentence
    stmts = engine.add_statement("Supercalifragilisticexpialidocious")
    assert len(stmts) == 1
    assert stmts[0].statement_type == "UNPARSED"
    assert engine.is_consistent()


def test_query_disconnected_nodes():
    engine = TemporalReasoningEngine()
    engine.add_statement("NodeA before NodeB.")
    engine.add_statement("IslandC before IslandD.")
    # Between NodeA and IslandC there is no temporal connection
    assert engine.query("NodeA", "IslandC") is None


def test_four_node_strict_cycle():
    # N1 -> N2 -> N3 -> N4 -> N1
    engine = TemporalReasoningEngine()
    engine.add_statement("N1 before N2.")
    engine.add_statement("N2 before N3.")
    engine.add_statement("N3 before N4.")
    engine.add_statement("N4 before N1.")
    assert not engine.is_consistent()
    conflicts = engine.check_consistency()
    assert any("cycle" in c.conflict_type.lower() for c in conflicts)


def test_instantaneous_event_bounds():
    ev = Event(
        event_id="E_inst",
        description="Flash",
        start_time=datetime(2026, 9, 3, 12, 0, 0),
        end_time=datetime(2026, 9, 3, 12, 0, 0),
    )
    assert ev.is_instantaneous
    assert ev.duration == timedelta(0)


def test_tricky_weekday_relative_normalization():
    # Anchor: Sunday 2026-09-06
    anchor = datetime(2026, 9, 6, 12, 0, 0)
    norm = normalize_text("We met last Monday.", anchor=anchor)
    assert len(norm) == 1
    assert norm[0].type == "RELATIVE_DATE"
    assert norm[0].resolved_datetime == datetime(2026, 8, 31, 12, 0, 0)


def test_multiple_sentences_in_one_block():
    engine = TemporalReasoningEngine()
    text = """
    Alpha happened before Beta.
    Beta happened before Gamma.
    Gamma happened before Delta.
    """
    engine.add_statement(text)
    assert engine.query("Alpha", "Delta") == TemporalRelation.BEFORE
    assert engine.query("Delta", "Alpha") == TemporalRelation.AFTER
