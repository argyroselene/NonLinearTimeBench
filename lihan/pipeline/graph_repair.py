"""Path-consistency repair (PCR): Allen's own 1983 algorithm, wired up as an
automatic repair stage in an LLM temporal-graph extraction pipeline.

Allen's path-consistency algorithm propagates the composition table over every
length-2 path in the interval network to detect contradictions: if rel(i,j)=R1
and rel(j,k)=R2, then rel(i,k) must be a member of compose(R1,R2) -- if the
predicted rel(i,k) isn't, that's a witnessed contradiction (a triangle where
the third edge disagrees with what the other two jointly imply). TLEX (arXiv
2406.05265) uses exactly this check to *detect* inconsistencies in LLM-
extracted TimeML graphs, but its own paper states automatic correction is
unexplored future work ("manually corrected"). This module is that missing
correction step: for a violated edge, every third node that witnesses the
violation casts a "vote" (compose(R1,R2)) for what the edge should be; if
every voting witness agrees on a nonempty common relation, the edge is
repaired to the vote-intersection member closest (by Allen conceptual-
neighborhood distance, `allen_relations.allen_distance`) to the model's
original prediction -- staying maximally faithful to the model's original,
evidence-grounded guess rather than overriding it with an arbitrary pick.
Edges with conflicting votes (empty intersection) are left unchanged and
logged, matching the honest scope-limitation style already used elsewhere in
this codebase (e.g. `awt_f1.py`'s node-correspondence handling) rather than
guessing.

A single witness triangle is not enough to trust a fix: in a closed 3-node
triangle where exactly one edge is genuinely wrong, path-consistency alone
can't tell *which* of the three is at fault (the two correct edges look just
as "inconsistent" from the wrong edge's point of view). Requiring at least
`_MIN_WITNESSES` independent third-node triangles to unanimously agree before
applying a fix is what turns this from a coin flip into real evidence -- a
single dissenting triangle only asserts that *some* edge in it is wrong, but
several independent triangles converging on the same relation is a genuine
majority signal, which is only available in a graph dense enough to give an
edge more than one witness (i.e. the story-level graphs this stage targets,
not a bare triangle). A single-witness violation is still logged (something
is locally inconsistent) but left unchanged for lack of corroborating
evidence, again rather than guessing. `_MAX_PASSES` is deliberately small and
paired with a full-graph state fingerprint: repairing one edge can newly
constrain another, but if two passes ever produce the exact same edge
assignment we're in a cycle (three edges of one triangle taking turns
"fixing" each other, chasing their own tails through no fault of any single
edge) and further iteration would only oscillate, never converge -- so the
loop stops the moment a repeat is detected rather than pass-count timing out
mid-cycle in an arbitrary, unstable state.
"""

from metrics.allen_composition import COMPOSITION, INVERSE
from metrics.allen_relations import RELATIONS, allen_distance

_MAX_PASSES = 5
_MIN_WITNESSES = 2


def _edge_map(edges):
    """{(i, j): relation} for both directions of every edge, using inverses."""
    mapping = {}
    for edge in edges:
        i, j, rel = edge["node_i"], edge["node_j"], edge["allen_relation"]
        mapping[(i, j)] = rel
        mapping[(j, i)] = INVERSE[rel]
    return mapping


def _vote_for_edge(i, k, node_ids, mapping):
    """All composition-table votes for rel(i, k) from third nodes j that connect to both."""
    votes = []
    for j in node_ids:
        if j == i or j == k:
            continue
        if (i, j) in mapping and (j, k) in mapping:
            votes.append(COMPOSITION[(mapping[(i, j)], mapping[(j, k)])])
    return votes


def _closest_relation(candidates, reference_relation):
    """Deterministic tie-break: candidate closest to the original prediction by
    Allen conceptual-neighborhood distance, then by canonical RELATIONS order."""
    return min(candidates, key=lambda r: (allen_distance(reference_relation, r), RELATIONS.index(r)))


def repair_edges(nodes, edges):
    """Path-consistency repair: detect and correct edges that contradict what
    other predicted edges jointly imply, via Allen's composition table.

    Returns (repaired_edges, repair_log). `repair_log` entries are
    {"edge": [node_i, node_j], "from_relation": ..., "to_relation": ..., "reason": ...}
    -- `to_relation` is None for a detected-but-unresolved conflict (witnesses'
    votes disagree with empty intersection, so the edge is left unchanged).
    """
    node_ids = {n["id"] for n in nodes}
    current = [
        dict(e) for e in edges
        if e.get("node_i") in node_ids
        and e.get("node_j") in node_ids
        and e.get("allen_relation") in RELATIONS
    ]
    repair_log = []
    logged_conflicts = set()
    seen_states = set()

    def _state_fingerprint():
        return frozenset((e["node_i"], e["node_j"], e["allen_relation"]) for e in current)

    for _ in range(_MAX_PASSES):
        state = _state_fingerprint()
        if state in seen_states:
            break
        seen_states.add(state)

        mapping = _edge_map(current)
        updates = {}
        for idx, edge in enumerate(current):
            i, k, rel = edge["node_i"], edge["node_j"], edge["allen_relation"]
            votes = _vote_for_edge(i, k, node_ids, mapping)
            if not votes:
                continue
            intersection = set.intersection(*(set(v) for v in votes))
            if rel in intersection:
                continue
            if intersection and len(votes) >= _MIN_WITNESSES:
                new_rel = _closest_relation(intersection, rel)
                updates[idx] = new_rel
                repair_log.append({
                    "edge": [i, k],
                    "from_relation": rel,
                    "to_relation": new_rel,
                    "reason": f"violates transitivity with {len(votes)} witness path(s) in agreement; "
                              f"repaired to closest consistent relation",
                })
            elif (i, k) not in logged_conflicts:
                logged_conflicts.add((i, k))
                if not intersection:
                    reason = (f"violates transitivity with {len(votes)} witness path(s) "
                              f"but they disagree (empty vote intersection); left unchanged")
                else:
                    reason = (f"violates transitivity with only {len(votes)} witness path(s) "
                              f"(< {_MIN_WITNESSES} needed for a confident fix); left unchanged")
                repair_log.append({
                    "edge": [i, k],
                    "from_relation": rel,
                    "to_relation": None,
                    "reason": reason,
                })

        if not updates:
            break
        for idx, new_rel in updates.items():
            current[idx]["allen_relation"] = new_rel

    return current, repair_log
