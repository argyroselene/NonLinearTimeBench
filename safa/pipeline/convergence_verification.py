"""Convergence-Order Consistency (COC): a deterministic verification stage for
LLM-proposed cross-thread convergence candidates.

Path-consistency repair (`graph_repair.py`) can verify same-thread Allen-
relation edges against each other because the predicted graph is dense with
same-thread triangles to check transitivity against. Cross-thread convergence
candidates have no such structure to lean on -- in practice the predicted
graph has zero cross-thread edges, so `candidate_convergence_pairs` is the
only cross-thread signal that exists at all, and there is nothing else to
verify it against.

What *is* available, for free, with no extra LLM call: each thread's own
chronological order, already computed by stage 3 (`topological_sort_per_thread`),
purely deterministically, before convergence is ever considered. If two
threads A and B have more than one candidate convergence anchor between them,
those anchors jointly claim a specific interleaving of A and B -- and that
claim can be internally contradictory even though each individual candidate
looks locally plausible. E.g. anchors (a2, b5) and (a7, b1) both being "the
same moment" would require b5 to come after b1 in one framing and before it in
another -- impossible. Among a set of mutually consistent anchors, the largest
such subset is the longest strictly-increasing subsequence of B-positions when
anchors are sorted by A-position; anything outside that subsequence is
rejected as contradicting its peers.

This also incidentally resolves the empirical many-to-one collapse failure
mode (several distinct A-nodes all "converging" with the same B-node): two
anchors sharing a B-position cannot both be part of a *strictly* increasing
subsequence, so at most one survives, without a separate dedup-by-target rule.

Everything else here is a basic sanity filter for malformed model output
(non-pairs, unknown node ids, same-thread "convergence", exact duplicates) --
none of it needs an LLM call, matching this codebase's existing pattern of
doing what deterministic code can do without one.

Live-model candidates arrive as groups (`{"members": [...], "shared_detail":
...}`) rather than pre-formed pairs, since asking the model to independently
guess a single partner for each flagged sentence -- rather than naming every
sentence that shares the moment in one judgment -- was found empirically to
cause systematic cross-thread mispairing (a flagged sentence gets linked to
the wrong sentence in the other thread even though the model correctly
flagged it). `_flatten_groups` expands each group into its N-choose-2
constituent pairs before the filters below run.
"""

from itertools import combinations


def _as_pair(candidate):
    """Accepts either a plain [node_i, node_j] pair (fixtures, gold data) or a
    live-LLM candidate object {"node_i": ..., "node_j": ..., "shared_detail":
    ...}. Returns (node_i, node_j) or None if the shape isn't recognized."""
    if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
        return candidate[0], candidate[1]
    if isinstance(candidate, dict) and "node_i" in candidate and "node_j" in candidate:
        return candidate["node_i"], candidate["node_j"]
    return None


def _flatten_groups(candidate_pairs):
    """Expands live-LLM group candidates {"members": [id, id, ...], "shared_detail":
    ...} into one node_i/node_j pair per unordered member combination, so a single
    "these N sentences are all the same moment" judgment -- which is how the model
    naturally reports multi-way convergence, and avoids forcing it to independently
    guess a partner for each anchor (the source of cross-thread mispairing) --
    becomes N-choose-2 ordinary pair candidates for the filters below. Non-group
    candidates (plain pairs, node_i/node_j objects) pass through unchanged; a
    "members" list with fewer than 2 entries is left as-is so it falls through to
    the malformed-candidate filter instead of silently vanishing."""
    flattened = []
    for candidate in candidate_pairs:
        if isinstance(candidate, dict) and isinstance(candidate.get("members"), (list, tuple)) \
                and len(candidate["members"]) >= 2:
            for a, b in combinations(candidate["members"], 2):
                flattened.append({"node_i": a, "node_j": b})
        else:
            flattened.append(candidate)
    return flattened


def _malformed_or_same_thread_filtered(nodes, candidate_pairs, log):
    """First three filters: shape, unknown ids, same-thread, dedup."""
    thread_of = {n["id"]: n["thread_id"] for n in nodes}
    seen = set()
    survivors = []
    for pair in candidate_pairs:
        parsed = _as_pair(pair)
        if parsed is None:
            log.append({"pair": pair, "kept": False,
                        "reason": "not a well-formed pair (expected exactly 2 node ids)"})
            continue
        a, b = parsed
        if a == b or a not in thread_of or b not in thread_of:
            log.append({"pair": [a, b], "kept": False,
                        "reason": "references an unknown or duplicate node id"})
            continue
        if thread_of[a] == thread_of[b]:
            log.append({"pair": [a, b], "kept": False,
                        "reason": "both nodes are in the same thread -- a node cannot converge with its own thread"})
            continue
        key = frozenset((a, b))
        if key in seen:
            log.append({"pair": [a, b], "kept": False, "reason": "exact duplicate of another candidate"})
            continue
        seen.add(key)
        survivors.append((a, b))
    return survivors


def _longest_increasing_subsequence_indices(values):
    """Longest strictly-increasing subsequence, returning the kept indices.

    When several subsequences tie at the maximum length, this returns the one
    made of the EARLIEST-proposed candidates. That tie-break matters: the
    previous implementation reconstructed from the smallest tail, which
    preferred later, smaller-valued candidates and could evict an already-kept
    correct anchor as soon as a new candidate arrived -- e.g. values [5] kept
    index 0, but [5, 1] kept only index 1, dropping the original. Since
    convergence recall is this pipeline's bottleneck and candidates arrive in
    the model's own order of salience, discarding the earlier one is the wrong
    default.

    n is the number of candidates between a single thread pair (a handful), so
    the quadratic reconstruction below is preferred over a subtler O(n log n)
    walk for being obviously correct.
    """
    if not values:
        return set()

    # lengths[i] = length of the longest increasing subsequence ending at i
    lengths = [1] * len(values)
    for i in range(len(values)):
        for j in range(i):
            if values[j] < values[i] and lengths[j] + 1 > lengths[i]:
                lengths[i] = lengths[j] + 1

    best = max(lengths)
    # earliest index that can end a maximal subsequence
    cur = min(i for i, length in enumerate(lengths) if length == best)

    kept = [cur]
    while lengths[cur] > 1:
        # earliest valid predecessor, again preferring earlier candidates
        cur = min(
            j for j in range(cur)
            if lengths[j] == lengths[cur] - 1 and values[j] < values[cur]
        )
        kept.append(cur)
    return set(kept)


def _order_consistency_filtered(thread_orders, survivors, log):
    """Fourth filter: keep the largest mutually order-consistent subset of
    candidates for each unordered thread-pair, via longest increasing
    subsequence over (position_in_a, position_in_b)."""
    position = {}
    for tid, order in thread_orders.items():
        for idx, node_id in enumerate(order):
            position[node_id] = idx

    groups = {}
    for a, b in survivors:
        tid_a = next(tid for tid, order in thread_orders.items() if a in order)
        tid_b = next(tid for tid, order in thread_orders.items() if b in order)
        key = frozenset((tid_a, tid_b))
        groups.setdefault(key, []).append((a, b, tid_a))

    verified = []
    for candidates in groups.values():
        if len(candidates) == 1:
            a, b, _ = candidates[0]
            verified.append([a, b])
            log.append({"pair": [a, b], "kept": True, "reason": "sole candidate between this thread pair"})
            continue

        # Orient every candidate the same way: (first_thread_node, second_thread_node)
        # using the pair's own first-seen thread as the sort axis, so positions
        # are comparable across candidates that share the same thread pair.
        anchor_thread = candidates[0][2]
        oriented = []
        for a, b, tid_a in candidates:
            if tid_a == anchor_thread:
                oriented.append((a, b))
            else:
                oriented.append((b, a))
        oriented.sort(key=lambda pair: position[pair[0]])
        b_positions = [position[pair[1]] for pair in oriented]
        kept_indices = _longest_increasing_subsequence_indices(b_positions)

        for idx, (a, b) in enumerate(oriented):
            if idx in kept_indices:
                verified.append([a, b])
                log.append({"pair": [a, b], "kept": True,
                            "reason": "order-consistent with the other convergence anchor(s) between these threads"})
            else:
                other_count = len(oriented) - 1
                log.append({"pair": [a, b], "kept": False,
                            "reason": f"breaks monotonic ordering with {other_count} other convergence "
                                      f"anchor(s) between the same threads"})

    return verified


def verify_convergence_points(nodes, thread_orders, candidate_pairs):
    """Filters LLM-proposed cross-thread convergence candidates down to a
    mutually consistent subset, using only already-computed per-thread orders
    -- no LLM call.

    Returns (verified_pairs, verification_log). `verification_log` entries are
    {"pair": [a, b], "kept": bool, "reason": ...}, covering both accepted and
    rejected candidates for transparency.
    """
    log = []
    flattened = _flatten_groups(candidate_pairs)
    survivors = _malformed_or_same_thread_filtered(nodes, flattened, log)
    verified = _order_consistency_filtered(thread_orders, survivors, log)
    return verified, log
