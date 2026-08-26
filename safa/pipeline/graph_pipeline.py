"""The 4-stage temporal-graph pipeline (plan section 4B).

Stages 1-2 call the LLM (structured JSON, constrained to the schemas in
schemas.py). Stages 3-4 are deterministic code -- no LLM involved -- so the
only thing that can vary run to run is what the model extracts in stages 1-2.

Each stage's output is kept in the returned result so stage-wise AWT-F1 can be
computed later against the gold JSON (plan's H3a diagnostic requirement).
"""

from graphlib import TopologicalSorter, CycleError

from pipeline.convergence_verification import verify_convergence_points
from pipeline.graph_repair import repair_edges
from pipeline.prompts import (
    node_extraction_prompt,
    edge_extraction_prompt,
    convergence_recall_critique_prompt,
)
from pipeline.schemas import (
    NODE_EXTRACTION_SCHEMA,
    EDGE_EXTRACTION_SCHEMA,
    CONVERGENCE_RECALL_CRITIQUE_SCHEMA,
)

# Allen relations that place node_i's start strictly before node_j's, and are
# thus usable as "i before j" edges for the per-thread topological sort, which
# orders events by when they begin.
#
#   before       i ends before j begins          -> i starts first
#   meets        i ends exactly as j begins      -> i starts first
#   overlaps     i begins, then j begins          -> i starts first
#   finished-by  same end, j begins later         -> i starts first
#
# `starts`/`started-by` are deliberately NOT here: they assert that both
# intervals begin at the same instant, so they carry no ordering information
# at all. Treating them as precedence (as this previously did) invented an
# arbitrary order between simultaneous events, which then propagated into the
# thread positions COC uses to verify convergence anchors. `equals` is
# excluded for the same reason.
_PRECEDENCE_RELATIONS = {"before", "meets", "finished-by", "overlaps"}
_INVERSE_PRECEDENCE_RELATIONS = {"after", "met-by", "finishes", "overlapped-by"}


def _thread_of(node_id, nodes_by_id):
    return nodes_by_id[node_id]["thread_id"]


def topological_sort_per_thread(nodes, edges):
    """Stage 3: deterministic per-thread ordering via Kahn's algorithm.

    Returns {thread_id: [node_id, ...]} in each thread's inferred chronological
    order. Edges that cross threads, or whose relation isn't a precedence
    relation, are ignored here -- cross-thread alignment is stage 4's job.
    """
    nodes_by_id = {n["id"]: n for n in nodes}
    threads = {}
    for n in nodes:
        threads.setdefault(n["thread_id"], set()).add(n["id"])

    sorters = {tid: TopologicalSorter() for tid in threads}
    for tid, ids in threads.items():
        for node_id in sorted(ids):
            sorters[tid].add(node_id)

    for edge in edges:
        i, j, rel = edge["node_i"], edge["node_j"], edge["allen_relation"]
        if i not in nodes_by_id or j not in nodes_by_id:
            continue
        if _thread_of(i, nodes_by_id) != _thread_of(j, nodes_by_id):
            continue
        tid = _thread_of(i, nodes_by_id)
        if rel in _PRECEDENCE_RELATIONS:
            sorters[tid].add(j, i)
        elif rel in _INVERSE_PRECEDENCE_RELATIONS:
            sorters[tid].add(i, j)

    orders = {}
    for tid, sorter in sorters.items():
        try:
            orders[tid] = list(sorter.static_order())
        except CycleError:
            orders[tid] = sorted(threads[tid])
    return orders


def align_convergence_points(thread_orders, convergence_points):
    """Stage 4: deterministic cross-thread merge via shared convergence points.

    Chains together per-thread orders at their convergence anchors: whenever
    two nodes from different threads are marked as the same moment, the
    threads are merged so nodes before/after the anchor in either thread stay
    on the correct side of it. Convergence pairs that don't reference known
    nodes are ignored.
    """
    position = {}
    for tid, order in thread_orders.items():
        for idx, node_id in enumerate(order):
            position[node_id] = (tid, idx)

    anchors = [
        pair for pair in convergence_points
        if len(pair) == 2 and pair[0] in position and pair[1] in position
    ]

    merged = []
    consumed = set()
    remaining_orders = {tid: list(order) for tid, order in thread_orders.items()}

    for a, b in anchors:
        for node_id in (a, b):
            if node_id in consumed:
                continue
            tid, _ = position[node_id]
            while remaining_orders[tid] and remaining_orders[tid][0] != node_id:
                head = remaining_orders[tid].pop(0)
                if head not in consumed:
                    merged.append(head)
                    consumed.add(head)
            if remaining_orders[tid] and remaining_orders[tid][0] == node_id:
                remaining_orders[tid].pop(0)
            if node_id not in consumed:
                merged.append(node_id)
                consumed.add(node_id)

    for tid in sorted(remaining_orders):
        for node_id in remaining_orders[tid]:
            if node_id not in consumed:
                merged.append(node_id)
                consumed.add(node_id)

    return merged


def _merge_convergence_candidates(flagged, missed):
    """Union two candidate-group lists, deduping by member set so a critique
    pass re-stating an already-flagged group doesn't double it up. Malformed
    groups (missing "members") are passed through rather than raising --
    verify_convergence_points already handles that shape defensively."""
    seen = {frozenset(g["members"]) for g in flagged if "members" in g}
    merged = list(flagged)
    for group in missed:
        if "members" not in group:
            merged.append(group)
            continue
        key = frozenset(group["members"])
        if key not in seen:
            seen.add(key)
            merged.append(group)
    return merged


def _finish_pipeline(nodes, raw_edges, raw_convergence_points):
    """Stages 3 onward (PCR, per-thread sort, COC, alignment) -- deterministic,
    no LLM involved. Factored out so run_graph_pipeline and
    run_graph_pipeline_matched share one implementation of "what happens
    after extraction," rather than a second copy drifting out of sync."""
    edges, repair_log = repair_edges(nodes, raw_edges)

    thread_orders = topological_sort_per_thread(nodes, edges)
    convergence_points, convergence_verification_log = verify_convergence_points(
        nodes, thread_orders, raw_convergence_points
    )
    global_order = align_convergence_points(thread_orders, convergence_points)

    return {
        "events": nodes,
        "edges": edges,
        "raw_edges": raw_edges,
        "repair_log": repair_log,
        "raw_convergence_points": raw_convergence_points,
        "candidate_convergence_pairs": raw_convergence_points,
        "convergence_verification_log": convergence_verification_log,
        "thread_orders": thread_orders,
        "global_order": global_order,
        "convergence_points": convergence_points,
    }


def run_graph_pipeline(passage, llm_client, use_recall_critique=False):
    """Runs all stages and returns every stage's output for diagnostic scoring.

    `passage` is a list of sentence strings (index 0 = sentence 1 = "s1").

    `use_recall_critique` (default False, so existing callers/results are
    unaffected unless they opt in): inserts stage 2.5, a second dedicated LLM
    call asking only "what convergence pairs did the previous pass miss"
    (`convergence_recall_critique_prompt`). Convergence-point recall is this
    pipeline's dominant empirical bottleneck (PLAN_AND_STATUS.md); PCR/COC
    downstream can only verify candidates that were proposed, never invent
    ones that weren't, so this stage targets recall specifically rather than
    consistency. Any additional candidates it finds are merged into the same
    raw candidate pool COC already verifies -- COC's deterministic
    order-consistency filter is unchanged and acts as the precision backstop
    against this stage's deliberately permissive prompt.

    NOTE: calling this twice (once per use_recall_critique value) to compare
    CRC on vs. off makes two INDEPENDENT node/edge-extraction calls, which is
    not a clean ablation on a hosted API -- see PLAN_AND_STATUS.md §5.3a for
    a documented case where that alone produced a scoring difference with no
    CRC involvement. Use run_graph_pipeline_matched for a fair comparison.
    """
    node_result = llm_client.complete(node_extraction_prompt(passage), NODE_EXTRACTION_SCHEMA)
    nodes = node_result["events"]

    edge_result = llm_client.complete(edge_extraction_prompt(passage, nodes), EDGE_EXTRACTION_SCHEMA)
    raw_edges = edge_result["edges"]
    raw_convergence_points = edge_result["candidate_convergence_pairs"]

    recall_critique_added = []
    if use_recall_critique:
        critique_result = llm_client.complete(
            convergence_recall_critique_prompt(passage, nodes, raw_convergence_points),
            CONVERGENCE_RECALL_CRITIQUE_SCHEMA,
        )
        recall_critique_added = critique_result["missed_convergence_pairs"]
        raw_convergence_points = _merge_convergence_candidates(raw_convergence_points, recall_critique_added)

    result = _finish_pipeline(nodes, raw_edges, raw_convergence_points)
    result["recall_critique_added"] = recall_critique_added
    return result


def run_graph_pipeline_matched(passage, llm_client):
    """Runs node + edge extraction ONCE, then produces both a no-CRC and a
    CRC result from that single shared extraction output -- differing only in
    whether the critique pass's extra candidates are merged in. This isolates
    CRC's own effect from LLM run-to-run non-determinism, which calling
    run_graph_pipeline() twice independently cannot do: PLAN_AND_STATUS.md
    §5.3a documents a real case where two separate edge-extraction calls for
    the same story (temperature 0) returned different convergence candidates,
    with no CRC involved at all, confounding that ablation.

    Costs 3 LLM calls total (node, edge, critique) to produce BOTH results --
    fewer than running run_graph_pipeline() twice (2 + 3 = 5), as well as
    being the statistically sound design.

    Returns (result_without_crc, result_with_crc).
    """
    node_result = llm_client.complete(node_extraction_prompt(passage), NODE_EXTRACTION_SCHEMA)
    nodes = node_result["events"]

    edge_result = llm_client.complete(edge_extraction_prompt(passage, nodes), EDGE_EXTRACTION_SCHEMA)
    raw_edges = edge_result["edges"]
    raw_convergence_points = edge_result["candidate_convergence_pairs"]

    critique_result = llm_client.complete(
        convergence_recall_critique_prompt(passage, nodes, raw_convergence_points),
        CONVERGENCE_RECALL_CRITIQUE_SCHEMA,
    )
    recall_critique_added = critique_result["missed_convergence_pairs"]
    merged_convergence_points = _merge_convergence_candidates(raw_convergence_points, recall_critique_added)

    result_without_crc = _finish_pipeline(nodes, raw_edges, raw_convergence_points)
    result_without_crc["recall_critique_added"] = []

    result_with_crc = _finish_pipeline(nodes, raw_edges, merged_convergence_points)
    result_with_crc["recall_critique_added"] = recall_critique_added

    return result_without_crc, result_with_crc
