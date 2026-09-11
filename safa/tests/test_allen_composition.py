import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from metrics.allen_composition import COMPOSITION, INVERSE, compose
from metrics.allen_relations import RELATIONS


def test_every_relation_pair_has_a_nonempty_composition():
    for r1 in RELATIONS:
        for r2 in RELATIONS:
            assert COMPOSITION[(r1, r2)], f"{r1} o {r2} produced no observed relations"


def test_equals_is_the_identity_element():
    for r in RELATIONS:
        assert compose("equals", r) == frozenset({r})
        assert compose(r, "equals") == frozenset({r})


def test_before_before_is_before():
    assert compose("before", "before") == frozenset({"before"})


def test_after_after_is_after():
    assert compose("after", "after") == frozenset({"after"})


def test_meets_meets_is_before():
    assert compose("meets", "meets") == frozenset({"before"})


def test_met_by_met_by_is_after():
    assert compose("met-by", "met-by") == frozenset({"after"})


def test_during_contains_is_fully_unconstrained():
    # A during B, B contains C: B's own extent tells us nothing about how A
    # (strictly inside B) relates to C (strictly inside B) -- every relation
    # between A and C remains possible.
    assert compose("during", "contains") == frozenset(RELATIONS)


def test_inverse_table_is_involutive():
    for r in RELATIONS:
        assert INVERSE[INVERSE[r]] == r


def test_composition_respects_inverse_symmetry():
    # rel(A,C) in R1 o R2  <=>  rel(C,A) in inverse(R2) o inverse(R1)
    for r1 in RELATIONS:
        for r2 in RELATIONS:
            forward = compose(r1, r2)
            backward = compose(INVERSE[r2], INVERSE[r1])
            assert forward == frozenset(INVERSE[r] for r in backward)
