"""
Temporal relation vocabulary and algebraic properties based on Allen's interval algebra
and point-temporal logic.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, Optional, Set, Tuple, Union


class TemporalRelation(str, Enum):
    """
    Standard temporal relations between events or intervals.
    Includes the 13 basic relations from Allen's Interval Algebra.
    """

    BEFORE = "before"
    AFTER = "after"
    EQUAL = "equal"
    MEETS = "meets"
    MET_BY = "met_by"
    OVERLAPS = "overlaps"
    OVERLAPPED_BY = "overlapped_by"
    DURING = "during"
    CONTAINS = "contains"
    STARTS = "starts"
    STARTED_BY = "started_by"
    FINISHES = "finishes"
    FINISHED_BY = "finished_by"

    def __str__(self) -> str:
        return self.value

    @property
    def inverse(self) -> TemporalRelation:
        """Return the algebraic inverse of this relation."""
        return INVERSE_MAP[self]

    @property
    def is_symmetric(self) -> bool:
        """True if the relation is identical to its inverse."""
        return self == TemporalRelation.EQUAL

    @property
    def is_strict_order(self) -> bool:
        """True if the relation represents a strict forward temporal ordering."""
        return self in {TemporalRelation.BEFORE, TemporalRelation.MEETS}


# Complete inverse mappings for all 13 relations
INVERSE_MAP: Dict[TemporalRelation, TemporalRelation] = {
    TemporalRelation.BEFORE: TemporalRelation.AFTER,
    TemporalRelation.AFTER: TemporalRelation.BEFORE,
    TemporalRelation.EQUAL: TemporalRelation.EQUAL,
    TemporalRelation.MEETS: TemporalRelation.MET_BY,
    TemporalRelation.MET_BY: TemporalRelation.MEETS,
    TemporalRelation.OVERLAPS: TemporalRelation.OVERLAPPED_BY,
    TemporalRelation.OVERLAPPED_BY: TemporalRelation.OVERLAPS,
    TemporalRelation.DURING: TemporalRelation.CONTAINS,
    TemporalRelation.CONTAINS: TemporalRelation.DURING,
    TemporalRelation.STARTS: TemporalRelation.STARTED_BY,
    TemporalRelation.STARTED_BY: TemporalRelation.STARTS,
    TemporalRelation.FINISHES: TemporalRelation.FINISHED_BY,
    TemporalRelation.FINISHED_BY: TemporalRelation.FINISHES,
}


def get_inverse(relation: Union[TemporalRelation, str]) -> TemporalRelation:
    """Return the inverse of a temporal relation."""
    rel = parse_relation(relation)
    return INVERSE_MAP[rel]


def parse_relation(val: Union[TemporalRelation, str]) -> TemporalRelation:
    """
    Parse a string or TemporalRelation enum into a TemporalRelation instance.
    Supports case-insensitivity and aliases (e.g. 'start' -> STARTS, 'finish' -> FINISHES).
    """
    if isinstance(val, TemporalRelation):
        return val

    norm = val.strip().lower().replace("-", "_").replace(" ", "_")

    alias_map: Dict[str, TemporalRelation] = {
        "before": TemporalRelation.BEFORE,
        "earlier": TemporalRelation.BEFORE,
        "precedes": TemporalRelation.BEFORE,
        "prior": TemporalRelation.BEFORE,
        "after": TemporalRelation.AFTER,
        "later": TemporalRelation.AFTER,
        "succeeds": TemporalRelation.AFTER,
        "following": TemporalRelation.AFTER,
        "equal": TemporalRelation.EQUAL,
        "equals": TemporalRelation.EQUAL,
        "same_time": TemporalRelation.EQUAL,
        "simultaneous": TemporalRelation.EQUAL,
        "meets": TemporalRelation.MEETS,
        "met_by": TemporalRelation.MET_BY,
        "overlaps": TemporalRelation.OVERLAPS,
        "overlapped_by": TemporalRelation.OVERLAPPED_BY,
        "during": TemporalRelation.DURING,
        "within": TemporalRelation.DURING,
        "contains": TemporalRelation.CONTAINS,
        "includes": TemporalRelation.CONTAINS,
        "starts": TemporalRelation.STARTS,
        "started_by": TemporalRelation.STARTED_BY,
        "finishes": TemporalRelation.FINISHES,
        "finished_by": TemporalRelation.FINISHED_BY,
    }

    if norm in alias_map:
        return alias_map[norm]

    # Try exact enum member name
    try:
        return TemporalRelation[val.strip().upper()]
    except KeyError:
        pass

    raise ValueError(f"Unknown temporal relation: '{val}'")


# Deterministic composition table for core combinations:
# Given (R1, R2), what possible relations R3 can hold such that A R1 B and B R2 C => A R3 C.
COMPOSITION_RULES: Dict[Tuple[TemporalRelation, TemporalRelation], Set[TemporalRelation]] = {
    # BEFORE compositions
    (TemporalRelation.BEFORE, TemporalRelation.BEFORE): {TemporalRelation.BEFORE},
    (TemporalRelation.BEFORE, TemporalRelation.MEETS): {TemporalRelation.BEFORE},
    (TemporalRelation.BEFORE, TemporalRelation.OVERLAPS): {TemporalRelation.BEFORE},
    (TemporalRelation.BEFORE, TemporalRelation.DURING): {TemporalRelation.BEFORE},
    (TemporalRelation.BEFORE, TemporalRelation.STARTS): {TemporalRelation.BEFORE},
    (TemporalRelation.BEFORE, TemporalRelation.EQUAL): {TemporalRelation.BEFORE},

    # MEETS compositions
    (TemporalRelation.MEETS, TemporalRelation.BEFORE): {TemporalRelation.BEFORE},
    (TemporalRelation.MEETS, TemporalRelation.MEETS): {TemporalRelation.BEFORE},
    (TemporalRelation.MEETS, TemporalRelation.EQUAL): {TemporalRelation.MEETS},

    # AFTER compositions
    (TemporalRelation.AFTER, TemporalRelation.AFTER): {TemporalRelation.AFTER},
    (TemporalRelation.AFTER, TemporalRelation.MET_BY): {TemporalRelation.AFTER},
    (TemporalRelation.AFTER, TemporalRelation.OVERLAPPED_BY): {TemporalRelation.AFTER},
    (TemporalRelation.AFTER, TemporalRelation.EQUAL): {TemporalRelation.AFTER},

    # DURING compositions
    (TemporalRelation.DURING, TemporalRelation.DURING): {TemporalRelation.DURING},
    (TemporalRelation.DURING, TemporalRelation.BEFORE): {TemporalRelation.BEFORE},
    (TemporalRelation.DURING, TemporalRelation.AFTER): {TemporalRelation.AFTER},
    (TemporalRelation.DURING, TemporalRelation.EQUAL): {TemporalRelation.DURING},

    # CONTAINS compositions
    (TemporalRelation.CONTAINS, TemporalRelation.CONTAINS): {TemporalRelation.CONTAINS},
    (TemporalRelation.CONTAINS, TemporalRelation.EQUAL): {TemporalRelation.CONTAINS},

    # EQUAL compositions
    (TemporalRelation.EQUAL, TemporalRelation.EQUAL): {TemporalRelation.EQUAL},
}

# Any relation R composed with EQUAL gives {R}, and EQUAL with R gives {R}
for r in TemporalRelation:
    COMPOSITION_RULES[(TemporalRelation.EQUAL, r)] = {r}
    COMPOSITION_RULES[(r, TemporalRelation.EQUAL)] = {r}


def compose_relations(r1: TemporalRelation, r2: TemporalRelation) -> Set[TemporalRelation]:
    """
    Return the set of valid composed relations for (r1, r2).
    Returns empty set if completely unconstrained or no deterministic inference exists.
    """
    return COMPOSITION_RULES.get((r1, r2), set())
