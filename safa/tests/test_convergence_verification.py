import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.convergence_verification import verify_convergence_points


def _nodes(**threads):
    """_nodes(A=["a1", "a2"], B=["b1", "b2"]) -> node dicts with thread_id set."""
    return [{"id": node_id, "thread_id": tid} for tid, ids in threads.items() for node_id in ids]


def _orders(**threads):
    return dict(threads)


def test_same_thread_candidate_is_dropped():
    nodes = _nodes(A=["a1", "a2"])
    orders = _orders(A=["a1", "a2"])
    verified, log = verify_convergence_points(nodes, orders, [["a1", "a2"]])
    assert verified == []
    assert log[0]["kept"] is False
    assert "same thread" in log[0]["reason"]


def test_live_llm_object_shaped_candidate_is_accepted():
    # Real LLM output is {"node_i", "node_j", "shared_detail"}, not a plain pair.
    nodes = _nodes(A=["a1"], B=["b1"])
    orders = _orders(A=["a1"], B=["b1"])
    candidate = {"node_i": "a1", "node_j": "b1", "shared_detail": "both describe the same explosion"}
    verified, log = verify_convergence_points(nodes, orders, [candidate])
    assert verified == [["a1", "b1"]]
    assert log[0]["kept"] is True


def test_group_candidate_is_expanded_into_pairwise_candidates():
    # Live LLM now reports "these sentences are all the same moment" as one
    # group rather than guessing a partner per sentence.
    nodes = _nodes(A=["a1"], B=["b1"], C=["c1"])
    orders = _orders(A=["a1"], B=["b1"], C=["c1"])
    group = {"members": ["a1", "b1", "c1"], "shared_detail": "all three threads witness the collapse"}
    verified, log = verify_convergence_points(nodes, orders, [group])
    assert {tuple(pair) for pair in verified} == {("a1", "b1"), ("a1", "c1"), ("b1", "c1")}
    assert all(entry["kept"] for entry in log)


def test_group_with_fewer_than_two_members_is_dropped_as_malformed():
    nodes = _nodes(A=["a1"], B=["b1"])
    orders = _orders(A=["a1"], B=["b1"])
    group = {"members": ["a1"], "shared_detail": "not enough to converge with"}
    verified, log = verify_convergence_points(nodes, orders, [group])
    assert verified == []
    assert log[0]["kept"] is False
    assert "well-formed pair" in log[0]["reason"]


def test_malformed_candidate_is_dropped():
    nodes = _nodes(A=["a1"], B=["b1"])
    orders = _orders(A=["a1"], B=["b1"])
    verified, log = verify_convergence_points(nodes, orders, [["a1", "b1", "extra"]])
    assert verified == []
    assert log[0]["kept"] is False
    assert "well-formed pair" in log[0]["reason"]


def test_unknown_node_candidate_is_dropped():
    nodes = _nodes(A=["a1"], B=["b1"])
    orders = _orders(A=["a1"], B=["b1"])
    verified, log = verify_convergence_points(nodes, orders, [["a1", "ghost"]])
    assert verified == []
    assert log[0]["kept"] is False


def test_exact_duplicate_candidate_is_dropped():
    nodes = _nodes(A=["a1"], B=["b1"])
    orders = _orders(A=["a1"], B=["b1"])
    verified, log = verify_convergence_points(nodes, orders, [["a1", "b1"], ["a1", "b1"]])
    assert verified == [["a1", "b1"]]
    dropped = [entry for entry in log if not entry["kept"]]
    assert len(dropped) == 1
    assert "duplicate" in dropped[0]["reason"]


def test_sole_candidate_between_a_thread_pair_is_kept():
    nodes = _nodes(A=["a1"], B=["b1"])
    orders = _orders(A=["a1"], B=["b1"])
    verified, log = verify_convergence_points(nodes, orders, [["a1", "b1"]])
    assert verified == [["a1", "b1"]]
    assert log[0]["kept"] is True


def test_order_consistent_anchors_are_both_kept():
    # a1 < a2 in A, b1 < b2 in B, and (a1,b1), (a2,b2) agree on the ordering.
    nodes = _nodes(A=["a1", "a2"], B=["b1", "b2"])
    orders = _orders(A=["a1", "a2"], B=["b1", "b2"])
    verified, log = verify_convergence_points(nodes, orders, [["a1", "b1"], ["a2", "b2"]])
    assert {tuple(pair) for pair in verified} == {("a1", "b1"), ("a2", "b2")}
    assert all(entry["kept"] for entry in log)


def test_order_contradictory_anchors_keep_only_the_longer_consistent_subsequence():
    # a1 < a2 in A, b1 < b2 in B. (a1, b2) and (a2, b1) jointly claim
    # b2 comes before b1 via a1<a2, contradicting B's own order -- impossible
    # for both to hold, so only one survives.
    nodes = _nodes(A=["a1", "a2"], B=["b1", "b2"])
    orders = _orders(A=["a1", "a2"], B=["b1", "b2"])
    verified, log = verify_convergence_points(nodes, orders, [["a1", "b2"], ["a2", "b1"]])
    assert len(verified) == 1
    kept = [entry for entry in log if entry["kept"]]
    dropped = [entry for entry in log if not entry["kept"]]
    assert len(kept) == 1
    assert len(dropped) == 1
    assert "breaks monotonic ordering" in dropped[0]["reason"]


def test_many_to_one_collapse_keeps_only_one_anchor():
    # Two distinct A-nodes both claim to converge with the same B-node --
    # strict-increase LIS can't keep both since they'd tie on b1's position.
    nodes = _nodes(A=["a1", "a2"], B=["b1"])
    orders = _orders(A=["a1", "a2"], B=["b1"])
    verified, log = verify_convergence_points(nodes, orders, [["a1", "b1"], ["a2", "b1"]])
    assert len(verified) == 1
    kept = [entry for entry in log if entry["kept"]]
    assert len(kept) == 1
