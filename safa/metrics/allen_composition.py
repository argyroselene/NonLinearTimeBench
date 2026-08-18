"""Allen's interval algebra: the composition (transitivity) table.

Given relation R1 = rel(A, B) and R2 = rel(B, C), the composition table answers
"what could rel(A, C) be?" -- usually not a single relation, since R1 and R2
alone rarely pin down A and C's relation exactly (e.g. `during` composed with
`contains` leaves A and C completely unconstrained: all 13 relations remain
possible). This is the classic table from Allen (1983), and it is the engine
behind `pipeline/graph_repair.py`'s path-consistency check: an edge (i, k)
that is inconsistent with the composition of edges (i, j) and (j, k) for some
third node j is a witnessed contradiction in the predicted graph.

Rather than hand-transcribing the published 13x13 table (error-prone to copy
and hard to eyeball-verify), this module derives it the same way
`allen_relations.py` derives its distance metric: directly from the formal
definition of each relation. B is fixed at a canonical position; every
integer-endpoint interval A within a bounded domain is classified against B
to find which ones satisfy rel(A,B)=R1, and likewise for C against rel(B,C)=R2;
the composition set for (R1, R2) is every rel(A,C) observed across that full
A-candidates x C-candidates enumeration. This is exhaustive (not sampled), so
boundary relations that require exact endpoint coincidence (meets, starts,
equals, ...) are reliably found rather than missed the way random sampling
would miss them (an exact integer coincidence has vanishing probability under
random draws, but is enumerated directly here). A fixed, generously-sized
domain makes the result deterministic and complete; the reference-identity
unit tests (`tests/test_allen_composition.py`) cross-check it against
hand-known facts (equals is the identity element, before-before=before,
meets-meets=before, during-contains=every relation) to catch derivation bugs.
"""

from metrics.allen_relations import RELATIONS

INVERSE = {
    "equals": "equals",
    "before": "after",
    "after": "before",
    "meets": "met-by",
    "met-by": "meets",
    "overlaps": "overlapped-by",
    "overlapped-by": "overlaps",
    "starts": "started-by",
    "started-by": "starts",
    "during": "contains",
    "contains": "during",
    "finishes": "finished-by",
    "finished-by": "finishes",
}

# B is anchored at (_SB, _EB) inside a domain wide enough to realize every
# relation on both sides of B (room to be strictly before, strictly after,
# and strictly nested within B's span) and to let A and C coincide exactly.
_DOMAIN_MAX = 15
_SB, _EB = 5, 10


def _classify(s1, e1, s2, e2):
    """rel(interval1=(s1,e1), interval2=(s2,e2)) from raw endpoints (s1<e1, s2<e2)."""
    if s1 == s2 and e1 == e2:
        return "equals"
    if e1 < s2:
        return "before"
    if e2 < s1:
        return "after"
    if e1 == s2:
        return "meets"
    if e2 == s1:
        return "met-by"
    if s1 == s2:
        return "starts" if e1 < e2 else "started-by"
    if e1 == e2:
        return "finishes" if s1 > s2 else "finished-by"
    if s1 < s2 and e2 < e1:
        return "contains"
    if s2 < s1 and e1 < e2:
        return "during"
    if s1 < s2 < e1 < e2:
        return "overlaps"
    if s2 < s1 < e2 < e1:
        return "overlapped-by"
    raise ValueError(f"unclassifiable endpoints: {(s1, e1, s2, e2)!r}")


def _build_composition_table():
    points = range(0, _DOMAIN_MAX + 1)
    pairs = [(s, e) for s in points for e in points if s < e]

    candidates_as_first = {r: [] for r in RELATIONS}   # (sA,eA) with rel(A,B)=r
    candidates_as_second = {r: [] for r in RELATIONS}  # (sC,eC) with rel(B,C)=r
    for s, e in pairs:
        candidates_as_first[_classify(s, e, _SB, _EB)].append((s, e))
        candidates_as_second[_classify(_SB, _EB, s, e)].append((s, e))

    table = {}
    for r1 in RELATIONS:
        for r2 in RELATIONS:
            observed = set()
            for sa, ea in candidates_as_first[r1]:
                for sc, ec in candidates_as_second[r2]:
                    observed.add(_classify(sa, ea, sc, ec))
            table[(r1, r2)] = frozenset(observed)
    return table


COMPOSITION = _build_composition_table()


def compose(relation_1, relation_2):
    """The set of relations rel(A, C) could be, given rel(A,B)=relation_1 and rel(B,C)=relation_2."""
    return COMPOSITION[(relation_1, relation_2)]
