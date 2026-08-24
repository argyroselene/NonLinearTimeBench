import json
import os

from pipeline.llm_client import FixtureLLMClient
from pipeline.direct_baseline import run_direct_baseline
from pipeline.graph_pipeline import (
    run_graph_pipeline,
    run_graph_pipeline_matched,
    topological_sort_per_thread,
    align_convergence_points,
)
from metrics.awt_f1 import awt_f1

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORY_PATH = os.path.join(ROOT, "data", "stories", "story_01", "original.json")


def load_story():
    with open(STORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def passage_from_story(story):
    by_id = {e["id"]: e for e in story["events"]}
    ordered_ids = sorted(by_id, key=lambda i: int(i[1:]))
    return [by_id[i]["text"] for i in ordered_ids]


def test_topological_sort_per_thread_orders_by_precedence_edges():
    nodes = [
        {"id": "s2", "thread_id": "L"},
        {"id": "s5", "thread_id": "L"},
        {"id": "s8", "thread_id": "L"},
    ]
    edges = [
        {"node_i": "s2", "node_j": "s5", "allen_relation": "before"},
        {"node_i": "s5", "node_j": "s8", "allen_relation": "before"},
    ]
    orders = topological_sort_per_thread(nodes, edges)
    assert orders["L"] == ["s2", "s5", "s8"]


def test_topological_sort_ignores_coincident_start_relations():
    """`starts` asserts both intervals BEGIN at the same instant, so it carries
    no ordering information. Treating it as precedence invented an arbitrary
    order between simultaneous events, which propagated into the thread
    positions COC uses to verify convergence anchors."""
    nodes = [{"id": "s1", "thread_id": "X"}, {"id": "s2", "thread_id": "X"}]
    orders = topological_sort_per_thread(
        nodes, [{"node_i": "s2", "node_j": "s1", "allen_relation": "starts"}]
    )
    # falls back to deterministic id order rather than asserting s2 precedes s1
    assert orders["X"] == ["s1", "s2"]


def test_topological_sort_keeps_finished_by_as_precedence():
    """`finished-by`: both end together but node_i begins first, so it DOES
    order by start time and must still count as precedence."""
    nodes = [{"id": "s1", "thread_id": "X"}, {"id": "s2", "thread_id": "X"}]
    orders = topological_sort_per_thread(
        nodes, [{"node_i": "s2", "node_j": "s1", "allen_relation": "finished-by"}]
    )
    assert orders["X"] == ["s2", "s1"]


def test_topological_sort_handles_inverse_precedence_relation():
    nodes = [{"id": "s1", "thread_id": "R"}, {"id": "s2", "thread_id": "R"}]
    edges = [{"node_i": "s1", "node_j": "s2", "allen_relation": "after"}]
    orders = topological_sort_per_thread(nodes, edges)
    assert orders["R"] == ["s2", "s1"]


def test_topological_sort_breaks_cycle_deterministically_instead_of_raising():
    nodes = [{"id": "s1", "thread_id": "X"}, {"id": "s2", "thread_id": "X"}]
    edges = [
        {"node_i": "s1", "node_j": "s2", "allen_relation": "before"},
        {"node_i": "s2", "node_j": "s1", "allen_relation": "before"},
    ]
    orders = topological_sort_per_thread(nodes, edges)
    assert orders["X"] == ["s1", "s2"]


def test_align_convergence_points_merges_threads_at_shared_anchor():
    thread_orders = {"A": ["a1", "a2"], "B": ["b1", "b2"]}
    merged = align_convergence_points(thread_orders, [["a2", "b1"]])
    assert merged.index("a1") < merged.index("a2")
    assert merged.index("b1") < merged.index("b2")
    assert abs(merged.index("a2") - merged.index("b1")) == 1


def test_align_convergence_points_ignores_unknown_pairs():
    thread_orders = {"A": ["a1", "a2"]}
    merged = align_convergence_points(thread_orders, [["a1", "unknown"]])
    assert set(merged) == {"a1", "a2"}


def test_run_direct_baseline_returns_scripted_response():
    fixture = {
        "events": [{"id": "s1", "thread_id": "A"}, {"id": "s2", "thread_id": "L"}],
        "global_order": ["s2", "s1"],
        "convergence_points": [],
    }
    client = FixtureLLMClient([fixture])
    result = run_direct_baseline(["sentence one", "sentence two"], client)
    assert result["global_order"] == ["s2", "s1"]
    assert len(client.calls) == 1


def test_run_graph_pipeline_end_to_end_against_story_01_matches_gold():
    story = load_story()
    passage = passage_from_story(story)

    node_response = {"events": [{"id": e["id"], "thread_id": e["thread_id"]} for e in story["events"]]}
    edge_response = {
        "edges": [
            {"node_i": e["node_i"], "node_j": e["node_j"], "allen_relation": e["allen_relation"]}
            for e in story["edges"]
        ],
        "candidate_convergence_pairs": story["convergence_points"],
    }
    client = FixtureLLMClient([node_response, edge_response])

    result = run_graph_pipeline(passage, client)

    assert len(client.calls) == 2
    assert result["events"] == node_response["events"]
    assert result["edges"] == edge_response["edges"]

    thread_of = {e["id"]: e["thread_id"] for e in story["events"]}
    precedes = {"before": 1, "meets": 1, "after": -1, "met-by": -1}
    for thread_id, order in result["thread_orders"].items():
        thread_events = [e["id"] for e in story["events"] if e["thread_id"] == thread_id]
        assert sorted(order) == sorted(thread_events), f"thread {thread_id} order is missing/extra nodes"
        position = {node_id: i for i, node_id in enumerate(order)}
        for edge in story["edges"]:
            direction = precedes.get(edge["allen_relation"])
            if direction is None:
                continue
            if thread_of[edge["node_i"]] != thread_id or thread_of[edge["node_j"]] != thread_id:
                continue
            if direction == 1:
                assert position[edge["node_i"]] < position[edge["node_j"]], (
                    f"{thread_id}: {edge['node_i']} should precede {edge['node_j']}"
                )
            else:
                assert position[edge["node_j"]] < position[edge["node_i"]], (
                    f"{thread_id}: {edge['node_j']} should precede {edge['node_i']}"
                )

    scores = awt_f1(story, result)
    assert scores["relation_score"] == 1.0
    assert scores["thread_attribution_accuracy"] == 1.0
    assert scores["convergence_f1"] == 1.0
    assert scores["awt_f1"] == 1.0


def test_run_graph_pipeline_partial_score_when_relation_is_a_near_miss():
    story = load_story()
    passage = passage_from_story(story)

    node_response = {"events": [{"id": e["id"], "thread_id": e["thread_id"]} for e in story["events"]]}
    degraded_edges = [dict(e) for e in story["edges"]]
    degraded_edges[0]["allen_relation"] = "meets"  # gold is "before" for s2/s5
    edge_response = {
        "edges": [
            {"node_i": e["node_i"], "node_j": e["node_j"], "allen_relation": e["allen_relation"]}
            for e in degraded_edges
        ],
        "candidate_convergence_pairs": story["convergence_points"],
    }
    client = FixtureLLMClient([node_response, edge_response])

    result = run_graph_pipeline(passage, client)
    scores = awt_f1(story, result)

    assert 0.0 < scores["relation_score"] < 1.0
    assert scores["thread_attribution_accuracy"] == 1.0


def test_recall_critique_is_off_by_default_and_costs_no_extra_call():
    story = load_story()
    passage = passage_from_story(story)
    node_response = {"events": [{"id": e["id"], "thread_id": e["thread_id"]} for e in story["events"]]}
    edge_response = {
        "edges": [
            {"node_i": e["node_i"], "node_j": e["node_j"], "allen_relation": e["allen_relation"]}
            for e in story["edges"]
        ],
        "candidate_convergence_pairs": [],
    }
    client = FixtureLLMClient([node_response, edge_response])

    result = run_graph_pipeline(passage, client)

    assert len(client.calls) == 2
    assert result["recall_critique_added"] == []


def test_recall_critique_recovers_a_convergence_point_the_edge_pass_missed():
    """Worked example: story_01's gold graph has one convergence point,
    [s8, s9]. Script the edge-extraction pass to miss it entirely (an empty
    candidate list -- the exact failure mode PLAN_AND_STATUS.md documents as
    this pipeline's dominant bottleneck), then script the recall-critique
    pass to find it on a dedicated second look. Without the critique pass,
    convergence_f1 would be 0.0 (gold non-empty, predicted empty); with it,
    COC verifies the recovered candidate is order-consistent and keeps it."""
    story = load_story()
    passage = passage_from_story(story)
    node_response = {"events": [{"id": e["id"], "thread_id": e["thread_id"]} for e in story["events"]]}
    edge_response = {
        "edges": [
            {"node_i": e["node_i"], "node_j": e["node_j"], "allen_relation": e["allen_relation"]}
            for e in story["edges"]
        ],
        "candidate_convergence_pairs": [],  # the miss: edge pass finds zero convergence candidates
    }
    critique_response = {
        "missed_convergence_pairs": [
            {"members": ["s8", "s9"], "shared_detail": "recovered on the dedicated recall pass"}
        ]
    }
    client = FixtureLLMClient([node_response, edge_response, critique_response])

    without_critique = run_graph_pipeline(passage, FixtureLLMClient([node_response, edge_response]))
    with_critique = run_graph_pipeline(passage, client, use_recall_critique=True)

    assert len(client.calls) == 3
    assert with_critique["recall_critique_added"] == critique_response["missed_convergence_pairs"]

    scores_without = awt_f1(story, without_critique)
    scores_with = awt_f1(story, with_critique)
    assert scores_without["convergence_f1"] == 0.0
    assert scores_with["convergence_f1"] == 1.0
    assert scores_with["awt_f1"] > scores_without["awt_f1"]


def test_run_graph_pipeline_matched_shares_one_extraction_for_both_conditions():
    """run_graph_pipeline_matched must call node/edge extraction exactly ONCE
    (not once per condition) so both the no-CRC and CRC results are forked
    from identical extraction output -- the whole point is eliminating the
    run-to-run non-determinism that independent run_graph_pipeline() calls
    can't control for (PLAN_AND_STATUS.md §5.3a)."""
    story = load_story()
    passage = passage_from_story(story)
    node_response = {"events": [{"id": e["id"], "thread_id": e["thread_id"]} for e in story["events"]]}
    edge_response = {
        "edges": [
            {"node_i": e["node_i"], "node_j": e["node_j"], "allen_relation": e["allen_relation"]}
            for e in story["edges"]
        ],
        "candidate_convergence_pairs": [],  # miss the gold convergence pair on purpose
    }
    critique_response = {
        "missed_convergence_pairs": [
            {"members": ["s8", "s9"], "shared_detail": "recovered on the shared critique pass"}
        ]
    }
    client = FixtureLLMClient([node_response, edge_response, critique_response])

    without_crc, with_crc = run_graph_pipeline_matched(passage, client)

    assert len(client.calls) == 3  # exactly one extraction pass total, not two
    assert without_crc["events"] == with_crc["events"] == node_response["events"]
    assert without_crc["edges"] == with_crc["edges"]
    assert without_crc["raw_edges"] == with_crc["raw_edges"] == edge_response["edges"]

    assert without_crc["recall_critique_added"] == []
    assert with_crc["recall_critique_added"] == critique_response["missed_convergence_pairs"]

    scores_without = awt_f1(story, without_crc)
    scores_with = awt_f1(story, with_crc)
    assert scores_without["convergence_f1"] == 0.0
    assert scores_with["convergence_f1"] == 1.0
