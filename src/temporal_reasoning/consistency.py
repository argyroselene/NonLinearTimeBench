"""
Temporal consistency checker module.
Detects contradictions in temporal graphs including direct relation conflicts,
strict partial-order cycles, and timestamp bound inversions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from temporal_reasoning.events import Event
from temporal_reasoning.relations import TemporalRelation
from temporal_reasoning.graph import TemporalGraph, TemporalEdge


@dataclass
class TemporalConflict:
    """
    Representation of a detected temporal conflict or contradiction.

    Attributes:
        conflict_type: Classification of contradiction.
        event_ids: The event IDs involved in the conflict.
        message: Human-readable explanation.
        details: Additional contextual data.
    """

    conflict_type: str
    event_ids: List[str]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "event_ids": self.event_ids,
            "message": self.message,
            "details": self.details,
        }


class ConsistencyChecker:
    """Validates the logical consistency of temporal graphs and event bounds."""

    def __init__(self):
        # Disjoint relations that cannot simultaneously hold between distinct events
        self.disjoint_pairs = {
            (TemporalRelation.BEFORE, TemporalRelation.AFTER),
            (TemporalRelation.BEFORE, TemporalRelation.EQUAL),
            (TemporalRelation.BEFORE, TemporalRelation.DURING),
            (TemporalRelation.AFTER, TemporalRelation.EQUAL),
            (TemporalRelation.AFTER, TemporalRelation.DURING),
            (TemporalRelation.MEETS, TemporalRelation.BEFORE),
            (TemporalRelation.MEETS, TemporalRelation.AFTER),
        }

    def check(self, graph: TemporalGraph) -> List[TemporalConflict]:
        """Inspect the graph and return all detected conflicts."""
        conflicts: List[TemporalConflict] = []

        # 1. Event internal timestamp sanity
        for ev in graph.events.values():
            if ev.start_time and ev.end_time and ev.start_time > ev.end_time:
                conflicts.append(
                    TemporalConflict(
                        conflict_type="TIMESTAMP_INVERSION",
                        event_ids=[ev.event_id],
                        message=f"Event {ev.event_id} ({ev.description}) has start_time {ev.start_time} after end_time {ev.end_time}",
                    )
                )

        # 2. Pairwise direct relation contradictions between u and v
        events = list(graph.events.keys())
        for i in range(len(events)):
            u = events[i]
            for j in range(len(events)):
                v = events[j]
                if u == v:
                    rels = graph.get_relations_between(u, u)
                    for r in rels:
                        if r in (TemporalRelation.BEFORE, TemporalRelation.AFTER, TemporalRelation.MEETS):
                            conflicts.append(
                                TemporalConflict(
                                    conflict_type="SELF_LOOP_CONFLICT",
                                    event_ids=[u],
                                    message=f"Event {u} cannot have strict relation '{r.value}' to itself",
                                )
                            )
                else:
                    rels = graph.get_relations_between(u, v)
                    for r1, r2 in self.disjoint_pairs:
                        if r1 in rels and r2 in rels:
                            conflicts.append(
                                TemporalConflict(
                                    conflict_type="DISJOINT_RELATIONS",
                                    event_ids=[u, v],
                                    message=f"Conflicting relations between {u} and {v}: both {r1.value} and {r2.value} asserted",
                                    details={"relations": [r1.value, r2.value]},
                                )
                            )

                    # Bidirectional contradiction: A BEFORE B and B BEFORE A
                    u_before_v = TemporalRelation.BEFORE in rels
                    v_before_u = TemporalRelation.BEFORE in graph.get_relations_between(v, u)
                    if u_before_v and v_before_u:
                        conflicts.append(
                            TemporalConflict(
                                conflict_type="MUTUAL_BEFORE_CONFLICT",
                                event_ids=[u, v],
                                message=f"Mutual BEFORE conflict: {u} is before {v} and {v} is before {u}",
                            )
                        )

        # 3. Cycle detection in strict order relations (BEFORE, MEETS)
        cycle = self._find_strict_cycle(graph)
        if cycle:
            conflicts.append(
                TemporalConflict(
                    conflict_type="STRICT_ORDER_CYCLE",
                    event_ids=cycle,
                    message=f"Detected cyclic temporal ordering: {' -> '.join(cycle)}",
                    details={"cycle": cycle},
                )
            )

        # 4. Timestamp vs Graph relation mismatch
        for edge in graph.get_all_edges():
            ev_src = graph.get_event(edge.source_id)
            ev_tgt = graph.get_event(edge.target_id)
            if ev_src and ev_tgt:
                if edge.relation == TemporalRelation.BEFORE:
                    if (
                        ev_src.start_time
                        and ev_tgt.end_time
                        and ev_src.start_time >= ev_tgt.end_time
                    ):
                        conflicts.append(
                            TemporalConflict(
                                conflict_type="RELATION_TIMESTAMP_MISMATCH",
                                event_ids=[ev_src.event_id, ev_tgt.event_id],
                                message=(
                                    f"Edge asserts {ev_src.event_id} BEFORE {ev_tgt.event_id}, "
                                    f"but start {ev_src.start_time} >= end {ev_tgt.end_time}"
                                ),
                            )
                        )

        # Deduplicate conflicts
        seen_msgs = set()
        deduped = []
        for c in conflicts:
            if c.message not in seen_msgs:
                seen_msgs.add(c.message)
                deduped.append(c)

        return deduped

    def is_consistent(self, graph: TemporalGraph) -> bool:
        """Return True if the graph is free of contradictions."""
        return len(self.check(graph)) == 0

    def _find_strict_cycle(self, graph: TemporalGraph) -> Optional[List[str]]:
        """DFS cycle detection over strict ordering edges (BEFORE, MEETS)."""
        adj: Dict[str, List[str]] = {}
        for edge in graph.get_all_edges():
            if edge.relation in (TemporalRelation.BEFORE, TemporalRelation.MEETS):
                adj.setdefault(edge.source_id, []).append(edge.target_id)

        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        parent_map: Dict[str, str] = {}

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    res = dfs(neighbor, path + [neighbor])
                    if res:
                        return res
                elif neighbor in rec_stack:
                    # Found cycle
                    idx = path.index(neighbor) if neighbor in path else 0
                    return path[idx:] + [neighbor]

            rec_stack.remove(node)
            return None

        for n in list(graph.events.keys()):
            if n not in visited:
                res = dfs(n, [n])
                if res:
                    return res

        return None
