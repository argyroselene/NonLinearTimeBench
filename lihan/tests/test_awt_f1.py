import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from metrics.awt_f1 import (
    relation_score,
    thread_attribution_accuracy,
    convergence_f1,
    convergence_scores,
    pooled_convergence_f1,
    harmonic_mean,
    awt_f1,
    memorization_gap,
)


GOLD = {
    "events": [
        {"id": "s2", "thread_id": "L"},
        {"id": "s5", "thread_id": "L"},
        {"id": "s3", "thread_id": "S"},
        {"id": "s6", "thread_id": "S"},
    ],
    "edges": [
        {"node_i": "s2", "node_j": "s5", "allen_relation": "before"},
        {"node_i": "s3", "node_j": "s6", "allen_relation": "before"},
    ],
    "convergence_points": [["s8", "s9"]],
}


def test_relation_score_perfect_prediction():
    predicted_edges = [
        {"node_i": "s2", "node_j": "s5", "allen_relation": "before"},
        {"node_i": "s3", "node_j": "s6", "allen_relation": "before"},
    ]
    assert relation_score(GOLD["edges"], predicted_edges) == 1.0


def test_relation_score_near_miss_partial_credit():
    predicted_edges = [
        {"node_i": "s2", "node_j": "s5", "allen_relation": "meets"},  # near miss
        {"node_i": "s3", "node_j": "s6", "allen_relation": "before"},  # exact
    ]
    score = relation_score(GOLD["edges"], predicted_edges)
    assert 0.5 < score < 1.0


def test_relation_score_missing_edge_scores_zero_for_that_edge():
    predicted_edges = [
        {"node_i": "s2", "node_j": "s5", "allen_relation": "before"},
        # s3->s6 edge missing entirely
    ]
    score = relation_score(GOLD["edges"], predicted_edges)
    assert score == 0.5


def test_relation_score_reversed_node_order_scores_the_inverse_relation():
    """(s5, s2, "after") asserts exactly what gold's (s2, s5, "before") does --
    same temporal fact, opposite node order -- so it must score 1.0. Comparing
    the raw label instead gave 0.333 and penalised a correct answer."""
    predicted_edges = [
        {"node_i": "s5", "node_j": "s2", "allen_relation": "after"},
        {"node_i": "s6", "node_j": "s3", "allen_relation": "after"},
    ]
    assert relation_score(GOLD["edges"], predicted_edges) == 1.0


def test_relation_score_reversed_order_with_same_label_is_now_a_mismatch():
    """The flip side: (s5, s2, "before") claims s5 precedes s2, the OPPOSITE
    of gold. It must not score 1.0 just because the label text matches."""
    predicted_edges = [
        {"node_i": "s5", "node_j": "s2", "allen_relation": "before"},
        {"node_i": "s3", "node_j": "s6", "allen_relation": "before"},
    ]
    score = relation_score(GOLD["edges"], predicted_edges)
    assert score < 1.0


def test_relation_score_falls_back_to_global_order_when_no_explicit_edge():
    """A method that emits no explicit relations but does produce a final
    ordering still asserts a before/after for every pair in that ordering, and
    is scored on it -- the same basis the direct baseline is scored on."""
    order = ["s2", "s5", "s3", "s6"]
    assert relation_score(GOLD["edges"], [], global_order=order) == 1.0
    assert relation_score(GOLD["edges"], []) == 0.0  # without the order, nothing to score


def test_explicit_edge_takes_precedence_over_global_order():
    """An explicit Allen relation is more expressive than a coarse
    before/after read off the ordering, so it wins when both are available."""
    predicted_edges = [{"node_i": "s2", "node_j": "s5", "allen_relation": "meets"}]
    order = ["s2", "s5", "s3", "s6"]
    score = relation_score(GOLD["edges"], predicted_edges, global_order=order)
    # s2->s5 scored as the near-miss "meets" (5/6), s3->s6 derived from order (1.0)
    assert 0.9 < score < 1.0


def test_relation_score_empty_gold_is_vacuously_correct():
    assert relation_score([], [{"node_i": "a", "node_j": "b", "allen_relation": "before"}]) == 1.0


def test_thread_attribution_accuracy_all_correct():
    predicted_events = [
        {"id": "s2", "thread_id": "L"},
        {"id": "s5", "thread_id": "L"},
        {"id": "s3", "thread_id": "S"},
        {"id": "s6", "thread_id": "S"},
    ]
    assert thread_attribution_accuracy(GOLD["events"], predicted_events) == 1.0


def test_thread_attribution_accuracy_partial():
    predicted_events = [
        {"id": "s2", "thread_id": "L"},
        {"id": "s5", "thread_id": "WRONG"},
        {"id": "s3", "thread_id": "S"},
        {"id": "s6", "thread_id": "S"},
    ]
    assert thread_attribution_accuracy(GOLD["events"], predicted_events) == 0.75


def test_thread_attribution_missing_node_counts_as_incorrect():
    predicted_events = [
        {"id": "s2", "thread_id": "L"},
        {"id": "s3", "thread_id": "S"},
        {"id": "s6", "thread_id": "S"},
    ]
    assert thread_attribution_accuracy(GOLD["events"], predicted_events) == 0.75


def test_thread_attribution_is_label_invariant():
    # A model that clusters events correctly but invents its own thread
    # vocabulary (never matching gold's "L"/"S" strings) should still score
    # perfectly, since what matters is the induced partition, not the label text.
    predicted_events = [
        {"id": "s2", "thread_id": "Farrow_thread"},
        {"id": "s5", "thread_id": "Farrow_thread"},
        {"id": "s3", "thread_id": "Dawson_thread"},
        {"id": "s6", "thread_id": "Dawson_thread"},
    ]
    assert thread_attribution_accuracy(GOLD["events"], predicted_events) == 1.0


def test_thread_attribution_label_invariant_partial_mismatch():
    # Correct clustering under a different vocabulary, except one event
    # (s6) is misassigned into the other predicted cluster.
    predicted_events = [
        {"id": "s2", "thread_id": "alpha"},
        {"id": "s5", "thread_id": "alpha"},
        {"id": "s3", "thread_id": "beta"},
        {"id": "s6", "thread_id": "alpha"},
    ]
    assert thread_attribution_accuracy(GOLD["events"], predicted_events) == 0.75


def test_convergence_f1_perfect():
    p, r, f1 = convergence_f1([["s8", "s9"]], [["s9", "s8"]])
    assert (p, r, f1) == (1.0, 1.0, 1.0)


def test_convergence_f1_hallucinated_pair_hurts_precision():
    p, r, f1 = convergence_f1([["s8", "s9"]], [["s8", "s9"], ["s1", "s2"]])
    assert p == 0.5
    assert r == 1.0


def test_convergence_f1_missed_pair_hurts_recall():
    p, r, f1 = convergence_f1([["s8", "s9"], ["s1", "s2"]], [["s8", "s9"]])
    assert p == 1.0
    assert r == 0.5


def test_convergence_f1_accepts_raw_candidate_groups():
    """Raw pre-verification output is a list of {"members": [...]} groups, not
    flat pairs. These used to collapse to frozenset of the DICT KEYS, matching
    nothing and scoring a silent 0.0 -- which is why every stored
    awt_f1_scores_unrepaired was exactly 0.0 and every repair_delta was
    meaningless. A 3-member group expands to its 3 pairwise combinations."""
    groups = [{"members": ["s8", "s9"], "shared_detail": "same alarm"}]
    p, r, f1 = convergence_f1([["s8", "s9"]], groups)
    assert (p, r, f1) == (1.0, 1.0, 1.0)

    three = [{"members": ["s5", "s6", "s25"], "shared_detail": "x"}]
    p, r, _ = convergence_f1([["s5", "s6"], ["s5", "s25"]], three)
    assert r == 1.0          # both gold pairs recovered from the group
    assert p == pytest.approx(2 / 3)  # s6/s25 pair is a false positive


def test_convergence_f1_rejects_unrecognised_entry_instead_of_scoring_zero():
    with pytest.raises(TypeError):
        convergence_f1([["s1", "s2"]], ["not-a-pair-object"])


def test_closure_aware_precision_does_not_punish_unannotated_true_pairs():
    """The core fix. Gold annotates only the salient moments, but the intervals
    imply many more true simultaneities. A model proposing a genuinely
    simultaneous pair that nobody annotated must not be scored as wrong --
    the sparse-annotation artifact TB-Dense was built to address."""
    salient = [["s26", "s15"]]
    pool = [["s26", "s15"], ["s14", "s32"], ["s21", "s26"]]
    proposed = [["s14", "s32"], ["s21", "s26"]]  # both true, neither annotated

    scores = convergence_scores(salient, proposed, pool)
    assert scores["convergence_precision_vs_pool"] == 1.0  # both genuinely valid
    assert scores["convergence_recall_salient"] == 0.0     # but missed the salient one

    # the old metric called both proposals false positives
    _, _, old_f1 = convergence_f1(salient, proposed)
    assert old_f1 == 0.0


def test_closure_aware_precision_still_penalises_genuinely_wrong_pairs():
    salient = [["s26", "s15"]]
    pool = [["s26", "s15"], ["s14", "s32"]]
    proposed = [["s14", "s32"], ["s1", "s99"]]  # one valid, one invented
    scores = convergence_scores(salient, proposed, pool)
    assert scores["convergence_precision_vs_pool"] == 0.5


def test_closure_aware_flags_when_no_pool_is_available():
    """Hand-authored stories have no machine-readable intervals, so precision
    cannot distinguish 'wrong' from 'unannotated' and must say so."""
    scores = convergence_scores([["s1", "s2"]], [["s3", "s4"]], valid_pool=None)
    assert scores["convergence_pool_available"] is False


def test_headline_core_score_is_not_annihilated_by_a_convergence_miss():
    """A 1-3 item convergence estimate must not zero out a 46-edge relation
    estimate and a 36-event thread estimate."""
    predicted = {
        "events": GOLD["events"],
        "edges": GOLD["edges"],
        "convergence_points": [],  # total convergence failure
    }
    result = awt_f1(GOLD, predicted)
    assert result["relation_score"] == 1.0
    assert result["thread_attribution_accuracy"] == 1.0
    assert result["awt_core"] == 1.0            # reflects what was actually measured well
    assert result["awt_f1_legacy_harmonic"] == 0.0  # the old artifact, kept for audit


def test_convergence_f1_both_empty_is_vacuously_correct():
    assert convergence_f1([], []) == (1.0, 1.0, 1.0)


def test_convergence_f1_hallucination_against_empty_gold_scores_zero():
    assert convergence_f1([], [["a", "b"]]) == (0.0, 0.0, 0.0)


def test_pooled_convergence_f1_pools_across_stories_instead_of_per_story():
    # story_a misses its only gold pair (per-story F1 would be 0.0);
    # story_b hits its only gold pair (per-story F1 would be 1.0). Per-story
    # scoring would report two noisy extremes; pooled scoring reflects the
    # true 1-of-2 recall across the dataset.
    story_results = [
        ("story_a", [["s8", "s9"]], []),
        ("story_b", [["s3", "s4"]], [["s3", "s4"]]),
    ]
    result = pooled_convergence_f1(story_results)
    assert result["n_gold_pairs"] == 2
    assert result["n_predicted_pairs"] == 1
    assert result["precision"] == 1.0
    assert result["recall"] == 0.5
    assert abs(result["f1"] - (2 / 3)) < 1e-9


def test_pooled_convergence_f1_namespaces_ids_so_same_ids_across_stories_dont_collide():
    # Both stories use the literal ids "s1"/"s2" for an unrelated pair; if ids
    # weren't namespaced by story_id, story_a's hallucinated pair would look
    # like a true positive against story_b's real gold pair.
    story_results = [
        ("story_a", [], [["s1", "s2"]]),
        ("story_b", [["s1", "s2"]], []),
    ]
    result = pooled_convergence_f1(story_results)
    assert result["n_gold_pairs"] == 1
    assert result["n_predicted_pairs"] == 1
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0


def test_pooled_convergence_f1_both_empty_is_vacuously_correct():
    result = pooled_convergence_f1([("story_a", [], []), ("story_b", [], [])])
    assert (result["precision"], result["recall"], result["f1"]) == (1.0, 1.0, 1.0)
    assert result["n_gold_pairs"] == 0


def test_harmonic_mean_matches_hand_calculation():
    # H(0.5, 1.0, 1.0) = 3 / (1/0.5 + 1/1.0 + 1/1.0) = 3 / 4 = 0.75
    assert harmonic_mean([0.5, 1.0, 1.0]) == 0.75


def test_harmonic_mean_zero_component_gives_zero():
    assert harmonic_mean([0.0, 1.0, 1.0]) == 0.0


def test_awt_f1_end_to_end_perfect_prediction():
    predicted = {
        "events": GOLD["events"],
        "edges": GOLD["edges"],
        "convergence_points": GOLD["convergence_points"],
    }
    result = awt_f1(GOLD, predicted)
    assert result["awt_f1"] == 1.0
    assert result["relation_score"] == 1.0
    assert result["thread_attribution_accuracy"] == 1.0
    assert result["convergence_f1"] == 1.0


def test_awt_f1_diagnostic_breakdown_isolates_failure_stage():
    predicted = {
        "events": GOLD["events"],
        "edges": GOLD["edges"],
        "convergence_points": [],  # only convergence detection fails
    }
    result = awt_f1(GOLD, predicted)
    assert result["relation_score"] == 1.0
    assert result["thread_attribution_accuracy"] == 1.0
    assert result["convergence_f1"] == 0.0
    assert result["awt_f1"] == 0.0  # harmonic mean punishes the zero component


def test_memorization_gap_is_original_minus_counterfactual():
    original = {"awt_f1": 0.8, "relation_score": 0.9}
    counterfactual = {"awt_f1": 0.5, "relation_score": 0.6}
    gap = memorization_gap(original, counterfactual)
    assert abs(gap["awt_f1"] - 0.3) < 1e-9
    assert abs(gap["relation_score"] - 0.3) < 1e-9
