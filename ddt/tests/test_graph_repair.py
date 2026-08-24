import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.graph_repair import repair_edges


def _nodes(*ids):
    return [{"id": node_id} for node_id in ids]


def test_consistent_triangle_is_left_unchanged():
    nodes = _nodes("i", "j", "k")
    edges = [
        {"node_i": "i", "node_j": "j", "allen_relation": "before"},
        {"node_i": "j", "node_j": "k", "allen_relation": "before"},
        {"node_i": "i", "node_j": "k", "allen_relation": "before"},
    ]
    repaired, log = repair_edges(nodes, edges)
    assert log == []
    assert {(e["node_i"], e["node_j"]): e["allen_relation"] for e in repaired} == {
        ("i", "j"): "before",
        ("j", "k"): "before",
        ("i", "k"): "before",
    }


def test_violation_confirmed_by_two_independent_witnesses_is_corrected_exactly():
    # Two separate triangles (via j1 and via j2) both compute
    # meets o meets = before (unique) for i-k. i-k is predicted "after",
    # contradicting both -- with 2 independent witnesses in agreement this
    # clears the confidence bar and gets repaired to "before".
    nodes = _nodes("i", "j1", "j2", "k")
    edges = [
        {"node_i": "i", "node_j": "j1", "allen_relation": "meets"},
        {"node_i": "j1", "node_j": "k", "allen_relation": "meets"},
        {"node_i": "i", "node_j": "j2", "allen_relation": "meets"},
        {"node_i": "j2", "node_j": "k", "allen_relation": "meets"},
        {"node_i": "i", "node_j": "k", "allen_relation": "after"},
    ]
    repaired, log = repair_edges(nodes, edges)
    fixed = {(e["node_i"], e["node_j"]): e["allen_relation"] for e in repaired}
    assert fixed[("i", "k")] == "before"
    ik_entries = [entry for entry in log if entry["edge"] == ["i", "k"]]
    assert ik_entries[0]["from_relation"] == "after"
    assert ik_entries[0]["to_relation"] == "before"


def test_single_witness_violation_is_flagged_but_left_unchanged():
    # Only one triangle (via j) witnesses i-k. A single triangle can't tell
    # us *which* of its three edges is the wrong one -- e.g. this could just
    # as easily mean i-j or j-k is wrong instead -- so a lone dissenting
    # witness isn't enough corroborating evidence to act on: the violation is
    # logged, but i-k is left exactly as predicted.
    nodes = _nodes("i", "j", "k")
    edges = [
        {"node_i": "i", "node_j": "j", "allen_relation": "meets"},
        {"node_i": "j", "node_j": "k", "allen_relation": "meets"},
        {"node_i": "i", "node_j": "k", "allen_relation": "after"},
    ]
    repaired, log = repair_edges(nodes, edges)
    fixed = {(e["node_i"], e["node_j"]): e["allen_relation"] for e in repaired}
    assert fixed[("i", "k")] == "after"
    ik_entries = [entry for entry in log if entry["edge"] == ["i", "k"]]
    assert ik_entries[0]["to_relation"] is None
    assert ik_entries[0]["from_relation"] == "after"


def test_conflicting_witnesses_leave_edge_unchanged_and_logged():
    # Witness j1: before o before = before.
    # Witness j2: after o after = after.
    # {before} n {after} = empty -- no confident single fix, so i-k stays put.
    nodes = _nodes("i", "j1", "j2", "k")
    edges = [
        {"node_i": "i", "node_j": "j1", "allen_relation": "before"},
        {"node_i": "j1", "node_j": "k", "allen_relation": "before"},
        {"node_i": "i", "node_j": "j2", "allen_relation": "after"},
        {"node_i": "j2", "node_j": "k", "allen_relation": "after"},
        {"node_i": "i", "node_j": "k", "allen_relation": "meets"},
    ]
    repaired, log = repair_edges(nodes, edges)
    fixed = {(e["node_i"], e["node_j"]): e["allen_relation"] for e in repaired}
    assert fixed[("i", "k")] == "meets"
    conflict_entries = [entry for entry in log if entry["edge"] == ["i", "k"]]
    assert len(conflict_entries) == 1
    assert conflict_entries[0]["to_relation"] is None
    assert conflict_entries[0]["from_relation"] == "meets"
