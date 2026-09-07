import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.check_coverage import linear_matches_original
from scripts.split_stories import _build_linear_variant, split_one

_AUTHORING = {
    "story_id": "story_test", "cf_story_id": "story_test_cf",
    "title": "Test", "cf_title": "Test CF", "source": "unit test", "cf_source": "unit test cf",
    "threads": [
        {"id": "A", "label": "Thread A", "cf_label": "Thread A cf", "granularity": "hours"},
        {"id": "B", "label": "Thread B", "cf_label": "Thread B cf", "granularity": "hours"},
    ],
    "events": [
        {"id": "s1", "thread_id": "A", "time_expr": "t1", "cf_time_expr": "t1", "text": "A1", "cf_text": "A1cf"},
        {"id": "s2", "thread_id": "B", "time_expr": "t2", "cf_time_expr": "t2", "text": "B1", "cf_text": "B1cf"},
        {"id": "s3", "thread_id": "A", "time_expr": "t3", "cf_time_expr": "t3", "text": "A2", "cf_text": "A2cf"},
        {"id": "s4", "thread_id": "B", "time_expr": "t4", "cf_time_expr": "t4", "text": "B2", "cf_text": "B2cf"},
    ],
    "edges": [
        {"node_i": "s1", "node_j": "s3", "allen_relation": "before", "evidence_span": "A1..A2"},
        {"node_i": "s2", "node_j": "s4", "allen_relation": "before", "evidence_span": "B1..B2"},
        {"node_i": "s3", "node_j": "s4", "allen_relation": "equals", "evidence_span": "A2==B2"},
    ],
    "convergence_points": [["s3", "s4"]],
}


def test_linear_variant_relabels_events_into_gold_chronological_order():
    original, _ = split_one(_AUTHORING)
    linear = _build_linear_variant(original)

    # s2 (thread B, t2) has no precedence edge ordering it relative to s1 (thread A,
    # t1) except through the s3/s4 convergence anchor, so both valid orderings
    # (s1,s2 interleaved either way) keep s1 before s3 and s2 before s4, with s3/s4
    # merged at the convergence point.
    assert len(linear["events"]) == 4
    ids_in_order = [e["id"] for e in linear["events"]]
    assert ids_in_order == [f"s{i + 1}" for i in range(4)]

    # the two originally-simultaneous events (s3, s4) must land adjacent and the
    # convergence pair must be rewritten to reference the new ids.
    assert len(linear["convergence_points"]) == 1
    a, b = linear["convergence_points"][0]
    assert {linear["id_map_from_original"]["s3"], linear["id_map_from_original"]["s4"]} == {a, b}


def test_linear_variant_preserves_text_and_thread_assignment_per_event():
    original, _ = split_one(_AUTHORING)
    linear = _build_linear_variant(original)

    original_text_by_id = {e["id"]: (e["text"], e["thread_id"]) for e in original["events"]}
    for new_id, old_id in {v: k for k, v in linear["id_map_from_original"].items()}.items():
        linear_event = next(e for e in linear["events"] if e["id"] == new_id)
        assert (linear_event["text"], linear_event["thread_id"]) == original_text_by_id[old_id]


def test_linear_matches_original_accepts_a_correct_relabeling():
    original, _ = split_one(_AUTHORING)
    linear = _build_linear_variant(original)
    assert linear_matches_original(original, linear) is True


def test_linear_matches_original_rejects_a_tampered_edge():
    original, _ = split_one(_AUTHORING)
    linear = _build_linear_variant(original)
    linear["edges"][0]["allen_relation"] = "after"
    assert linear_matches_original(original, linear) is False


def test_linear_matches_original_rejects_a_missing_id_map():
    original, _ = split_one(_AUTHORING)
    linear = _build_linear_variant(original)
    del linear["id_map_from_original"]
    assert linear_matches_original(original, linear) is False
