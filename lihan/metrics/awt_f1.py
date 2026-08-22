"""AWT-F1 (Allen-Weighted Temporal Graph F1).

A diagnostic, partial-credit metric for scoring a predicted temporal graph
(from a direct baseline or the graph pipeline) against a gold temporal graph,
covering three things no single existing metric (Exact Match, Kendall's tau,
pairwise accuracy) combines: near-miss-aware relation scoring, thread
attribution, and cross-thread convergence detection.

Expected graph shape (matches the dataset schema in data/stories/*):

    {
        "events": [{"id": "s1", "thread_id": "L"}, ...],
        "edges": [{"node_i": "s1", "node_j": "s2", "allen_relation": "before"}, ...],
        "convergence_points": [["s8", "s9"], ...]
    }

Node IDs are sentence-anchored (see the plan's node-correspondence caveat):
gold and predicted events are matched by `id` directly rather than via
embedding-based alignment, which is an explicit scope limitation of the pilot
dataset, not a general solution to the node-correspondence problem tackled by
CALLMSAE's Hungarian Graph Similarity, the Set-Aligning Framework, or GEST.
"""

from itertools import permutations

from metrics.allen_relations import edge_score, inverse_relation


def _edge_map(edges):
    return {(e["node_i"], e["node_j"]): e["allen_relation"] for e in edges}


def relation_score(gold_edges, predicted_edges, global_order=None):
    """Average Allen-distance-weighted score over every gold edge.

    A gold edge stated in the opposite node order is the SAME temporal claim
    ("A before B" == "B after A"), so a reversed match is scored against the
    inverse of the predicted relation. Comparing the raw label instead
    penalises a fully correct answer for word order -- e.g. predicting
    (s2, s1, "after") for gold (s1, s2, "before") scored 0.333 rather than 1.0.

    `global_order` (optional): a method's final chronological ordering of node
    ids. When a gold pair has no explicitly predicted relation but both of its
    nodes appear in that ordering, the ordering itself determines a coarse
    before/after claim, and the method is scored on it. This exists because
    the direct baseline is scored entirely on order-derived relations (see
    scripts/generate_direct_baseline_predictions.py, which assigns a
    before/after to every gold pair from its global order), so scoring the
    graph pipeline only on its sparse explicit edge list -- while discarding
    the global order it also produces -- compared the two methods on
    structurally different outputs and made the baseline look far stronger
    than it is. Passing global_order puts both methods on the same footing.

    Returns 1.0 for an empty gold edge set (vacuously correct).
    """
    if not gold_edges:
        return 1.0
    predicted = _edge_map(predicted_edges)
    position = {node_id: i for i, node_id in enumerate(global_order)} if global_order else {}

    total = 0.0
    for e in gold_edges:
        i, j = e["node_i"], e["node_j"]
        if (i, j) in predicted:
            total += edge_score(e["allen_relation"], predicted[(i, j)])
        elif (j, i) in predicted:
            total += edge_score(e["allen_relation"], inverse_relation(predicted[(j, i)]))
        elif i in position and j in position:
            derived = "before" if position[i] < position[j] else "after"
            total += edge_score(e["allen_relation"], derived)
        else:
            total += 0.0
    return total / len(gold_edges)


def _best_thread_label_mapping(gold_events, predicted_events):
    """Best one-to-one correspondence from predicted thread labels to gold thread
    labels, maximizing co-occurrence over matched node ids.

    Thread labels are free text -- an LLM has no way to reproduce gold's exact
    label string ("L") even when its clustering of events into threads is
    perfectly correct, so thread attribution must be scored on the induced
    partition, not literal string equality. This brute-forces the assignment
    (thread counts are always small in this dataset); if a run somehow yields
    a very large label vocabulary (e.g. a broken prediction with a near-unique
    label per event) the candidate pool on the larger side is capped by
    co-occurrence strength to keep the permutation search bounded.
    """
    predicted_by_id = {e["id"]: e for e in predicted_events}
    pairs = []
    for gold_event in gold_events:
        predicted_event = predicted_by_id.get(gold_event["id"])
        if predicted_event is None:
            continue
        g, p = gold_event.get("thread_id"), predicted_event.get("thread_id")
        if g is not None and p is not None:
            pairs.append((g, p))

    gold_labels = sorted({g for g, _ in pairs})
    pred_labels = sorted({p for _, p in pairs})
    if not gold_labels or not pred_labels:
        return {}

    contingency = {}
    for g, p in pairs:
        contingency[(g, p)] = contingency.get((g, p), 0) + 1

    small, large = (gold_labels, pred_labels) if len(gold_labels) <= len(pred_labels) else (pred_labels, gold_labels)
    small_is_gold = small is gold_labels

    cap = max(len(small) + 4, 10)
    if len(large) > cap:
        overlap_of = lambda label: sum(
            count for (g, p), count in contingency.items()
            if (p if small_is_gold else g) == label
        )
        large = sorted(large, key=overlap_of, reverse=True)[:cap]

    best_score, best_perm = -1, None
    for perm in permutations(large, len(small)):
        score = 0
        for s_label, l_label in zip(small, perm):
            key = (s_label, l_label) if small_is_gold else (l_label, s_label)
            score += contingency.get(key, 0)
        if score > best_score:
            best_score, best_perm = score, perm

    mapping = {}
    for s_label, l_label in zip(small, best_perm):
        gold_label, predicted_label = (s_label, l_label) if small_is_gold else (l_label, s_label)
        mapping[predicted_label] = gold_label
    return mapping


def thread_attribution_accuracy(gold_events, predicted_events):
    """Fraction of gold events whose predicted thread, under the best label
    correspondence to gold's thread vocabulary, matches, by node id.

    A gold event with no matching predicted event id counts as incorrect.
    Returns 1.0 if there are no gold events.
    """
    if not gold_events:
        return 1.0
    predicted_by_id = {e["id"]: e for e in predicted_events}
    mapping = _best_thread_label_mapping(gold_events, predicted_events)
    correct = 0
    for gold_event in gold_events:
        predicted_event = predicted_by_id.get(gold_event["id"])
        if predicted_event is None:
            continue
        predicted_label = predicted_event.get("thread_id")
        if mapping.get(predicted_label) == gold_event.get("thread_id"):
            correct += 1
    return correct / len(gold_events)


def _normalize_pairs(pairs):
    """Normalize a convergence-point list into a set of unordered id pairs.

    Accepts both shapes the pipeline produces: flat `[a, b]` pairs (verified
    output) and `{"members": [...], "shared_detail": ...}` candidate groups
    (raw pre-verification output), expanding a group into all of its pairwise
    combinations.

    Passing a group dict here used to silently do `frozenset(dict)`, which
    iterates the dict's KEYS -- every group collapsed to
    frozenset({"members", "shared_detail"}), matched no gold pair, and scored
    a flat 0.0. That is why every stored `awt_f1_scores_unrepaired` is exactly
    0.0 and every reported `repair_delta` was meaningless. Unrecognised
    entries now raise rather than scoring as a silent zero.
    """
    normalized = set()
    for entry in pairs:
        if isinstance(entry, dict):
            members = entry.get("members", [])
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    normalized.add(frozenset((members[i], members[j])))
        elif isinstance(entry, (list, tuple, set, frozenset)):
            normalized.add(frozenset(entry))
        else:
            raise TypeError(
                f"convergence point must be a pair or a candidate group, got {type(entry).__name__}"
            )
    return normalized


def convergence_f1(gold_convergence_points, predicted_convergence_points):
    """Precision/recall/F1 over unordered convergence-point pairs.

    Returns (precision, recall, f1). If gold has no convergence points, f1 is
    1.0 when predicted also has none, else 0.0 (a hallucinated convergence is
    a real error, so this case is not vacuously correct).
    """
    gold_set = _normalize_pairs(gold_convergence_points)
    predicted_set = _normalize_pairs(predicted_convergence_points)

    if not gold_set and not predicted_set:
        return 1.0, 1.0, 1.0
    if not gold_set or not predicted_set:
        return 0.0, 0.0, 0.0

    true_positives = len(gold_set & predicted_set)
    precision = true_positives / len(predicted_set)
    recall = true_positives / len(gold_set)
    if precision + recall == 0:
        return precision, recall, 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def scored_edges(gold_edges, predicted_edges, global_order=None):
    """Per-gold-edge scoring detail for reporting and the web UI.

    Mirrors relation_score's matching rules exactly, so the rendered per-edge
    view can never disagree with the headline number: an explicit prediction
    wins, a reversed-orientation prediction is compared against its inverse
    ("A before B" == "B after A"), and otherwise a coarse before/after is read
    off `global_order` if the method produced one.

    Lives here rather than being copy-pasted into each generation script --
    seven copies had drifted with the uninverted-reverse-match bug baked in.
    """
    predicted = {(e["node_i"], e["node_j"]): e["allen_relation"] for e in predicted_edges}
    position = {node_id: i for i, node_id in enumerate(global_order)} if global_order else {}

    scored = []
    for e in gold_edges:
        i, j = e["node_i"], e["node_j"]
        if (i, j) in predicted:
            relation, source = predicted[(i, j)], "explicit"
        elif (j, i) in predicted:
            relation, source = inverse_relation(predicted[(j, i)]), "explicit-reversed"
        elif i in position and j in position:
            relation = "before" if position[i] < position[j] else "after"
            source = "derived-from-order"
        else:
            relation, source = None, "missing"

        scored.append({
            "node_i": i,
            "node_j": j,
            "gold_relation": e["allen_relation"],
            "predicted_relation": relation,
            "predicted_from": source,
            "score": edge_score(e["allen_relation"], relation) if relation else 0.0,
        })
    return scored


def pooled_convergence_f1(story_results):
    """Dataset-level convergence precision/recall/F1, pooling convergence
    pairs across every story instead of computing F1 per story.

    Most stories have only 1-2 gold convergence points, so a per-story
    convergence_f1 is a high-variance statistic quantized to a handful of
    values (0, 0.4, 0.5, 0.57, 0.67, 1.0...) -- it lands on exactly 0
    whenever that tiny sample misses, which then zeroes the harmonic-mean
    AWT-F1 headline regardless of how good relation_score/thread_attribution
    (each computed over 30-50 edges/events -- much more stable) were for that
    story. Pooling gives convergence recall a real sample size across the
    whole dataset, the standard micro-averaging fix for a rare-event metric
    with too few positives per group to score individually.

    `story_results` is a list of (story_id, gold_convergence_points,
    predicted_convergence_points) tuples. Node ids are namespaced by
    story_id before pooling, since "s1" in one story and "s1" in another are
    different events and must never collide in the pooled set.

    Returns {"precision", "recall", "f1", "n_gold_pairs", "n_predicted_pairs"}.
    """
    gold_pooled = set()
    predicted_pooled = set()
    for story_id, gold_points, predicted_points in story_results:
        gold_pooled |= {frozenset((story_id, n) for n in pair) for pair in gold_points}
        predicted_pooled |= {frozenset((story_id, n) for n in pair) for pair in predicted_points}

    if not gold_pooled and not predicted_pooled:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "n_gold_pairs": 0, "n_predicted_pairs": 0}
    if not gold_pooled or not predicted_pooled:
        return {
            "precision": 0.0, "recall": 0.0, "f1": 0.0,
            "n_gold_pairs": len(gold_pooled), "n_predicted_pairs": len(predicted_pooled),
        }

    true_positives = len(gold_pooled & predicted_pooled)
    precision = true_positives / len(predicted_pooled)
    recall = true_positives / len(gold_pooled)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {
        "precision": precision, "recall": recall, "f1": f1,
        "n_gold_pairs": len(gold_pooled), "n_predicted_pairs": len(predicted_pooled),
    }


def convergence_scores(gold_salient, predicted, valid_pool=None):
    """Closure-aware convergence scoring (TempEval-3's temporal-awareness idea,
    UzZaman & Allen ACL 2011, adapted to same-moment detection).

    The plain precision/recall/F1 in convergence_f1 assumes the gold set is
    exhaustive. It is not: a story annotates the handful of NARRATIVELY salient
    shared moments, while the intervals themselves imply many more genuinely
    simultaneous cross-thread pairs (65 vs 3 annotated in story_06). Scoring
    exact set match therefore marks a model WRONG for correctly identifying a
    true simultaneity nobody bothered to annotate -- the sparse-annotation
    artifact TB-Dense (Cassidy et al. ACL 2014) was built to address.

    So the two questions are separated, because they are not the same question:

      precision_vs_pool  -- of the pairs the model proposed, how many are
                            genuinely simultaneous? Judged against `valid_pool`,
                            every formally valid simultaneity derivable from the
                            event intervals. Finding an unannotated true pair is
                            not penalised.
      recall_salient     -- of the moments the story marks as narratively
                            important, how many did the model find?

    They are deliberately NOT combined into one F1: a precision measured over
    ~5 proposals and a recall measured over ~3 gold items answer different
    questions at wildly different sample sizes, and averaging them produces a
    number that means nothing.

    `valid_pool` is omitted for stories whose gold was hand-authored without
    machine-readable intervals; precision then falls back to the salient set
    and is flagged, since it cannot distinguish "wrong" from "unannotated".
    """
    salient = _normalize_pairs(gold_salient)
    proposed = _normalize_pairs(predicted)
    pool = _normalize_pairs(valid_pool) if valid_pool else None

    recall_salient = len(proposed & salient) / len(salient) if salient else 1.0

    if pool is None:
        precision_basis = salient
        pool_available = False
    else:
        precision_basis = pool | salient
        pool_available = True
    precision = len(proposed & precision_basis) / len(proposed) if proposed else (1.0 if not salient else 0.0)

    return {
        "convergence_precision_vs_pool": precision,
        "convergence_recall_salient": recall_salient,
        "convergence_pool_available": pool_available,
        "n_proposed": len(proposed),
        "n_salient": len(salient),
        "n_pool": len(pool) if pool else 0,
    }


def harmonic_mean(scores):
    """Harmonic mean of a list of non-negative scores; 0.0 if any score is 0."""
    if not scores:
        return 0.0
    if any(s <= 0 for s in scores):
        return 0.0
    n = len(scores)
    return n / sum(1.0 / s for s in scores)


def awt_f1(gold, predicted):
    """Compute AWT-F1 and its diagnostic sub-scores for one gold/predicted graph pair.

    Returns a dict: relation_score, thread_attribution_accuracy,
    convergence_precision, convergence_recall, convergence_f1, awt_f1.
    """
    rel_score = relation_score(
        gold.get("edges", []),
        predicted.get("edges", []),
        global_order=predicted.get("global_order"),
    )
    thread_score = thread_attribution_accuracy(
        gold.get("events", []), predicted.get("events", [])
    )
    conv_precision, conv_recall, conv_f1 = convergence_f1(
        gold.get("convergence_points", []), predicted.get("convergence_points", [])
    )
    closure_aware = convergence_scores(
        gold.get("convergence_points", []),
        predicted.get("convergence_points", []),
        gold.get("convergence_pool"),
    )

    # Headline over the two sub-scores that are actually well-sampled:
    # relation_score is estimated over ~40-50 gold edges and thread accuracy
    # over 36-45 events, so both are stable. Convergence is estimated from 1-3
    # annotated items per story, and folding that into a harmonic mean let a
    # tiny, high-variance estimate annihilate two solid ones -- every story
    # with a convergence miss reported exactly 0.000 regardless of how good
    # the rest was. Aggregating incommensurable sub-scores this way is
    # criticised directly in the benchmark-methodology literature
    # ("How not to Lie with a Benchmark", arXiv:2112.01342; Colombo et al.,
    # arXiv:2202.03799). Convergence is reported alongside, not inside.
    core = harmonic_mean([rel_score, thread_score])

    result = {
        "relation_score": rel_score,
        "thread_attribution_accuracy": thread_score,
        "awt_core": core,
        "convergence_precision": conv_precision,
        "convergence_recall": conv_recall,
        "convergence_f1": conv_f1,
        # Retained so previously reported figures remain reproducible and the
        # revision is auditable, but it is the artifact-prone number described
        # above and should not be quoted as the headline.
        "awt_f1_legacy_harmonic": harmonic_mean([rel_score, thread_score, conv_f1]),
    }
    result.update(closure_aware)
    result["awt_f1"] = result["awt_f1_legacy_harmonic"]
    return result


def memorization_gap(awt_f1_original, awt_f1_counterfactual):
    """Delta-AWT-F1 = AWT-F1(original) - AWT-F1(counterfactual), for the overall score
    and every sub-score, given two awt_f1() result dicts."""
    return {
        key: awt_f1_original[key] - awt_f1_counterfactual[key]
        for key in awt_f1_original
    }
