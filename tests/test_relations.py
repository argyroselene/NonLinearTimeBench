"""Tests for the Temporal Relation vocabulary and algebraic properties."""

import pytest
from temporal_reasoning.relations import (
    TemporalRelation,
    get_inverse,
    parse_relation,
    compose_relations,
)


def test_relation_enum_values():
    assert TemporalRelation.BEFORE.value == "before"
    assert TemporalRelation.AFTER.value == "after"
    assert TemporalRelation.EQUAL.value == "equal"
    assert TemporalRelation.MEETS.value == "meets"
    assert TemporalRelation.DURING.value == "during"


def test_inverse_mappings():
    assert get_inverse(TemporalRelation.BEFORE) == TemporalRelation.AFTER
    assert get_inverse(TemporalRelation.AFTER) == TemporalRelation.BEFORE
    assert get_inverse(TemporalRelation.EQUAL) == TemporalRelation.EQUAL
    assert get_inverse(TemporalRelation.DURING) == TemporalRelation.CONTAINS
    assert get_inverse(TemporalRelation.CONTAINS) == TemporalRelation.DURING
    assert get_inverse(TemporalRelation.MEETS) == TemporalRelation.MET_BY
    assert get_inverse(TemporalRelation.STARTS) == TemporalRelation.STARTED_BY
    assert get_inverse(TemporalRelation.FINISHES) == TemporalRelation.FINISHED_BY

    # Double inverse property: inv(inv(R)) == R
    for rel in TemporalRelation:
        assert rel.inverse.inverse == rel


def test_parse_relation_aliases():
    assert parse_relation("before") == TemporalRelation.BEFORE
    assert parse_relation("BEFORE") == TemporalRelation.BEFORE
    assert parse_relation("earlier") == TemporalRelation.BEFORE
    assert parse_relation("precedes") == TemporalRelation.BEFORE
    assert parse_relation("succeeds") == TemporalRelation.AFTER
    assert parse_relation("simultaneous") == TemporalRelation.EQUAL
    assert parse_relation("within") == TemporalRelation.DURING
    assert parse_relation("includes") == TemporalRelation.CONTAINS

    with pytest.raises(ValueError, match="Unknown temporal relation"):
        parse_relation("somewhere_in_space")


def test_composition_transitivity():
    # A BEFORE B and B BEFORE C => A BEFORE C
    assert compose_relations(TemporalRelation.BEFORE, TemporalRelation.BEFORE) == {TemporalRelation.BEFORE}

    # A AFTER B and B AFTER C => A AFTER C
    assert compose_relations(TemporalRelation.AFTER, TemporalRelation.AFTER) == {TemporalRelation.AFTER}

    # A DURING B and B DURING C => A DURING C
    assert compose_relations(TemporalRelation.DURING, TemporalRelation.DURING) == {TemporalRelation.DURING}

    # Equality composition identity
    for rel in TemporalRelation:
        assert compose_relations(TemporalRelation.EQUAL, rel) == {rel}
        assert compose_relations(rel, TemporalRelation.EQUAL) == {rel}
