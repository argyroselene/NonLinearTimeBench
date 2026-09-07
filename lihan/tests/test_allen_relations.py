import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from metrics.allen_relations import RELATIONS, allen_distance, edge_score, MAX_DISTANCE


def test_all_13_relations_present():
    assert len(RELATIONS) == 13
    assert len(set(RELATIONS)) == 13


def test_distance_to_self_is_zero():
    for r in RELATIONS:
        assert allen_distance(r, r) == 0
        assert edge_score(r, r) == 1.0


def test_distance_is_symmetric():
    for r1 in RELATIONS:
        for r2 in RELATIONS:
            assert allen_distance(r1, r2) == allen_distance(r2, r1)


def test_before_meets_is_a_near_miss():
    # before: s1<e1<s2<e2 ; meets: s1<e1=s2<e2 -- only the (e1,s2) pair changes.
    assert allen_distance("before", "meets") == 1
    assert edge_score("before", "meets") == 1 - 1 / MAX_DISTANCE


def test_before_after_are_maximally_far():
    # before and after reverse every relative order between the two intervals'
    # endpoints -- this should be the largest disagreement in the table.
    d = allen_distance("before", "after")
    assert d == max(
        allen_distance("before", other) for other in RELATIONS if other != "before"
    )


def test_before_during_is_a_structural_error_not_a_near_miss():
    d_meets = allen_distance("before", "meets")
    d_during = allen_distance("before", "during")
    assert d_during > d_meets


def test_inverse_pairs_are_symmetric_in_distance_from_equals():
    # starts/started-by, finishes/finished-by, overlaps/overlapped-by,
    # meets/met-by, before/after should each be equidistant from "equals"
    # since they're mirror images of each other.
    pairs = [
        ("starts", "started-by"),
        ("finishes", "finished-by"),
        ("overlaps", "overlapped-by"),
        ("meets", "met-by"),
        ("before", "after"),
        ("during", "contains"),
    ]
    for a, b in pairs:
        assert allen_distance("equals", a) == allen_distance("equals", b)


def test_edge_score_bounds():
    for r1 in RELATIONS:
        for r2 in RELATIONS:
            score = edge_score(r1, r2)
            assert 0.0 <= score <= 1.0


def test_unknown_relation_raises():
    try:
        allen_distance("before", "sideways")
        assert False, "expected ValueError"
    except ValueError:
        pass
