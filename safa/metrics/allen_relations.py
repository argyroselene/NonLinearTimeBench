"""Allen's interval algebra: the 13 relations and a conceptual-neighborhood distance.

Every Allen relation between two intervals A=(s1,e1) and B=(s2,e2) is fully
characterized by the total order (with possible ties) of the four endpoints
s1, e1, s2, e2 (Allen, 1983; van Beek's point-algebra reduction). We encode
each relation as a rank assignment over {s1, e1, s2, e2} and define the
distance between two relations as the number of pairwise endpoint comparisons
(out of the 6 possible pairs) that disagree between them.

This distance is a principled stand-in for Freksa's (1992) conceptual
neighborhood graph: a single "continuous deformation" step between two
relations changes exactly one pairwise endpoint comparison (typically a `<`
becoming `=` or vice versa), so adjacent relations in the classic neighborhood
diagram are distance 1 apart under this metric, and it degrades gracefully
for relations that are not adjacent. It is derived directly from the formal
definition of the relations rather than hand-copied from a diagram, which
keeps it exact and unit-testable.
"""

from itertools import combinations

RELATIONS = [
    "equals",
    "before",
    "after",
    "meets",
    "met-by",
    "overlaps",
    "overlapped-by",
    "starts",
    "started-by",
    "during",
    "contains",
    "finishes",
    "finished-by",
]

# Rank of each endpoint (s1, e1, s2, e2) for each relation. Equal ranks mean
# the endpoints coincide.
_RANKS = {
    "equals": {"s1": 0, "s2": 0, "e1": 1, "e2": 1},
    "before": {"s1": 0, "e1": 1, "s2": 2, "e2": 3},
    "after": {"s2": 0, "e2": 1, "s1": 2, "e1": 3},
    "meets": {"s1": 0, "e1": 1, "s2": 1, "e2": 2},
    "met-by": {"s2": 0, "e2": 1, "s1": 1, "e1": 2},
    "overlaps": {"s1": 0, "s2": 1, "e1": 2, "e2": 3},
    "overlapped-by": {"s2": 0, "s1": 1, "e2": 2, "e1": 3},
    "starts": {"s1": 0, "s2": 0, "e1": 1, "e2": 2},
    "started-by": {"s1": 0, "s2": 0, "e2": 1, "e1": 2},
    "during": {"s2": 0, "s1": 1, "e1": 2, "e2": 3},
    "contains": {"s1": 0, "s2": 1, "e2": 2, "e1": 3},
    "finishes": {"s2": 0, "s1": 1, "e1": 2, "e2": 2},
    "finished-by": {"s1": 0, "s2": 1, "e1": 2, "e2": 2},
}

_POINTS = ("s1", "e1", "s2", "e2")
_PAIRS = list(combinations(_POINTS, 2))

MAX_DISTANCE = len(_PAIRS)  # 6: an upper bound on disagreeing pairs


def _comparison(ranks, p, q):
    if ranks[p] < ranks[q]:
        return "<"
    if ranks[p] > ranks[q]:
        return ">"
    return "="


def relation_from_intervals(a_start, a_end, b_start, b_end):
    """The Allen relation that holds between interval A and interval B.

    Derived from the same endpoint-comparison definition the rest of this
    module uses, so a gold label computed here is correct by construction
    rather than hand-asserted. This is what lets a story's gold graph be
    *generated* from the timeline its prose describes, instead of authored
    separately and hoped to agree -- and lets existing hand-written gold
    labels be checked against their own stated times.

    Intervals are closed and may be instantaneous (start == end).
    """
    if a_start > a_end or b_start > b_end:
        raise ValueError("interval end must not precede its start")

    ranks = {}
    for name, value in (("s1", a_start), ("e1", a_end), ("s2", b_start), ("e2", b_end)):
        ranks[name] = value

    target = tuple(_comparison(ranks, p, q) for p, q in _PAIRS)
    for relation, relation_ranks in _RANKS.items():
        if tuple(_comparison(relation_ranks, p, q) for p, q in _PAIRS) == target:
            return relation
    raise ValueError(
        f"no Allen relation matches intervals ({a_start},{a_end}) and ({b_start},{b_end})"
    )


def _derive_inverse_map():
    """Inverse of each relation, derived from _RANKS rather than hand-typed so
    it can never drift out of sync with the endpoint definitions.

    The inverse of a relation is what you get by swapping which interval is
    which: if A `before` B then B `after` A. Both statements assert the exact
    same temporal fact, so scoring must treat them as equivalent -- see
    relation_score's reversed-pair handling in metrics/awt_f1.py.
    """
    points = ("s1", "e1", "s2", "e2")
    swapped_name = {"s1": "s2", "e1": "e2", "s2": "s1", "e2": "e1"}

    def signature(ranks):
        return tuple(
            _comparison(ranks, p, q) for p, q in _PAIRS
        )

    by_signature = {signature(_RANKS[r]): r for r in RELATIONS}
    inverse = {}
    for relation, ranks in _RANKS.items():
        swapped = {swapped_name[point]: rank for point, rank in ranks.items()}
        inverse[relation] = by_signature[signature(swapped)]
    return inverse


INVERSE_RELATIONS = _derive_inverse_map()


def inverse_relation(relation):
    """The same temporal claim with the two intervals swapped (before <-> after)."""
    if relation not in INVERSE_RELATIONS:
        raise ValueError(f"unknown Allen relation: {relation!r}")
    return INVERSE_RELATIONS[relation]


def allen_distance(relation_a, relation_b):
    """Number of the 6 pairwise endpoint comparisons that differ between two relations."""
    if relation_a not in _RANKS:
        raise ValueError(f"unknown Allen relation: {relation_a!r}")
    if relation_b not in _RANKS:
        raise ValueError(f"unknown Allen relation: {relation_b!r}")
    ranks_a = _RANKS[relation_a]
    ranks_b = _RANKS[relation_b]
    return sum(
        1
        for p, q in _PAIRS
        if _comparison(ranks_a, p, q) != _comparison(ranks_b, p, q)
    )


def edge_score(gold_relation, predicted_relation):
    """Partial-credit score in [0, 1] for predicting `predicted_relation` when gold is `gold_relation`."""
    distance = allen_distance(gold_relation, predicted_relation)
    return max(0.0, 1.0 - distance / MAX_DISTANCE)
