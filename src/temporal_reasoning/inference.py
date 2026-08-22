"""
Symbolic temporal inference engine.
Applies deterministic inference rules including algebraic inversion,
transitivity closures, equality propagation, and interval boundary arithmetic.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from temporal_reasoning.events import Event
from temporal_reasoning.relations import (
    TemporalRelation,
    get_inverse,
    compose_relations,
)
from temporal_reasoning.graph import TemporalGraph, TemporalEdge


@dataclass
class InferenceResult:
    """Summary of an inference run."""

    iterations: int
    edges_added: int
    new_inferences: List[TemporalEdge]


class InferenceEngine:
    """Deterministic rule-based inference engine over temporal graphs."""

    def __init__(
        self,
        enable_inverse: bool = True,
        enable_transitivity: bool = True,
        enable_interval: bool = True,
        max_iterations: int = 50,
    ):
        self.enable_inverse = enable_inverse
        self.enable_transitivity = enable_transitivity
        self.enable_interval = enable_interval
        self.max_iterations = max_iterations

    def infer_inverses(self, graph: TemporalGraph) -> List[TemporalEdge]:
        """
        Derive inverse temporal relations for every directed edge in the graph.
        e.g. A BEFORE B => B AFTER A.
        """
        new_edges: List[TemporalEdge] = []
        current_edges = graph.get_all_edges()

        for edge in current_edges:
            inv_rel = get_inverse(edge.relation)
            existing_rels = graph.get_relations_between(edge.target_id, edge.source_id)
            if inv_rel not in existing_rels:
                inferred = graph.add_relation(
                    source=edge.target_id,
                    target=edge.source_id,
                    relation=inv_rel,
                    is_inferred=True,
                    confidence=edge.confidence,
                    provenance=f"Inverse of ({edge.source_id} {edge.relation.value} {edge.target_id})",
                )
                new_edges.append(inferred)

        return new_edges

    def infer_transitivity(self, graph: TemporalGraph) -> List[TemporalEdge]:
        """
        Derive composed transitive relations across paths (u -> v -> w).
        e.g. A BEFORE B and B BEFORE C => A BEFORE C.
        """
        new_edges: List[TemporalEdge] = []
        all_edges = graph.get_all_edges()

        # Group edges by source and target
        outgoing: Dict[str, List[TemporalEdge]] = {}
        for edge in all_edges:
            outgoing.setdefault(edge.source_id, []).append(edge)

        for edge1 in all_edges:
            u = edge1.source_id
            v = edge1.target_id
            r1 = edge1.relation

            for edge2 in outgoing.get(v, []):
                w = edge2.target_id
                r2 = edge2.relation
                if u == w:
                    continue

                composed_set = compose_relations(r1, r2)
                if len(composed_set) == 1:
                    r3 = next(iter(composed_set))
                    existing = graph.get_relations_between(u, w)
                    if r3 not in existing:
                        inferred = graph.add_relation(
                            source=u,
                            target=w,
                            relation=r3,
                            is_inferred=True,
                            confidence=min(edge1.confidence, edge2.confidence),
                            provenance=f"Transitivity: ({u} {r1.value} {v}) and ({v} {r2.value} {w})",
                        )
                        new_edges.append(inferred)

        return new_edges

    def infer_interval_bounds(self, graph: TemporalGraph) -> int:
        """
        Complete missing start_time, end_time, or duration for events with partial bounds.
        e.g. start + duration = end.
        """
        updated = 0
        for ev in graph.events.values():
            if ev.start_time and ev.duration and not ev.end_time:
                ev.end_time = ev.start_time + ev.duration
                updated += 1
            elif ev.end_time and ev.duration and not ev.start_time:
                ev.start_time = ev.end_time - ev.duration
                updated += 1
            elif ev.start_time and ev.end_time and not ev.duration:
                ev.duration = ev.end_time - ev.start_time
                updated += 1
        return updated

    def infer_relations_from_bounds(self, graph: TemporalGraph) -> List[TemporalEdge]:
        """
        Deduce temporal relations between events based on their concrete timestamps.
        """
        new_edges: List[TemporalEdge] = []
        events = list(graph.events.values())

        for i in range(len(events)):
            ev1 = events[i]
            for j in range(i + 1, len(events)):
                ev2 = events[j]

                # Both have start and end times => Full Allen interval deduction
                if ev1.start_time and ev1.end_time and ev2.start_time and ev2.end_time:
                    rel = self._deduce_allen_relation(ev1, ev2)
                    if rel:
                        if rel not in graph.get_relations_between(ev1.event_id, ev2.event_id):
                            new_edges.append(
                                graph.add_relation(
                                    ev1.event_id,
                                    ev2.event_id,
                                    rel,
                                    is_inferred=True,
                                    provenance=f"Interval bounds: {ev1.description} [{ev1.start_time.isoformat()}, {ev1.end_time.isoformat()}] vs {ev2.description} [{ev2.start_time.isoformat()}, {ev2.end_time.isoformat()}]",
                                )
                            )
                # Partial point bounds (e.g., ev1 ends before ev2 starts)
                elif ev1.end_time and ev2.start_time and ev1.end_time < ev2.start_time:
                    if TemporalRelation.BEFORE not in graph.get_relations_between(ev1.event_id, ev2.event_id):
                        new_edges.append(
                            graph.add_relation(
                                ev1.event_id,
                                ev2.event_id,
                                TemporalRelation.BEFORE,
                                is_inferred=True,
                                provenance=f"Timestamp bound: end {ev1.end_time} < start {ev2.start_time}",
                            )
                        )
                elif ev2.end_time and ev1.start_time and ev2.end_time < ev1.start_time:
                    if TemporalRelation.BEFORE not in graph.get_relations_between(ev2.event_id, ev1.event_id):
                        new_edges.append(
                            graph.add_relation(
                                ev2.event_id,
                                ev1.event_id,
                                TemporalRelation.BEFORE,
                                is_inferred=True,
                                provenance=f"Timestamp bound: end {ev2.end_time} < start {ev1.start_time}",
                            )
                        )

        return new_edges

    @staticmethod
    def _deduce_allen_relation(ev1: Event, ev2: Event) -> Optional[TemporalRelation]:
        """Compute the exact Allen relation between two fully bounded intervals."""
        s1, e1 = ev1.start_time, ev1.end_time
        s2, e2 = ev2.start_time, ev2.end_time
        if not (s1 and e1 and s2 and e2):
            return None

        if e1 < s2:
            return TemporalRelation.BEFORE
        if s1 > e2:
            return TemporalRelation.AFTER
        if e1 == s2:
            return TemporalRelation.MEETS
        if s1 == e2:
            return TemporalRelation.MET_BY
        if s1 == s2 and e1 == e2:
            return TemporalRelation.EQUAL
        if s1 == s2 and e1 < e2:
            return TemporalRelation.STARTS
        if s1 == s2 and e1 > e2:
            return TemporalRelation.STARTED_BY
        if s1 > s2 and e1 == e2:
            return TemporalRelation.FINISHES
        if s1 < s2 and e1 == e2:
            return TemporalRelation.FINISHED_BY
        if s2 < s1 and e1 < e2:
            return TemporalRelation.DURING
        if s1 < s2 and e2 < e1:
            return TemporalRelation.CONTAINS
        if s1 < s2 < e1 < e2:
            return TemporalRelation.OVERLAPS
        if s2 < s1 < e2 < e1:
            return TemporalRelation.OVERLAPPED_BY
        return None

    def step(self, graph: TemporalGraph) -> List[TemporalEdge]:
        """Execute a single round of inference rules."""
        inferred_this_step: List[TemporalEdge] = []

        if self.enable_interval:
            self.infer_interval_bounds(graph)
            bound_edges = self.infer_relations_from_bounds(graph)
            inferred_this_step.extend(bound_edges)

        if self.enable_inverse:
            inv_edges = self.infer_inverses(graph)
            inferred_this_step.extend(inv_edges)

        if self.enable_transitivity:
            trans_edges = self.infer_transitivity(graph)
            inferred_this_step.extend(trans_edges)

        return inferred_this_step

    def run(self, graph: TemporalGraph) -> InferenceResult:
        """Run inference rules to fixpoint or max iterations."""
        total_added = 0
        all_new: List[TemporalEdge] = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            new_edges = self.step(graph)
            if not new_edges:
                break
            total_added += len(new_edges)
            all_new.extend(new_edges)

        return InferenceResult(
            iterations=iteration,
            edges_added=total_added,
            new_inferences=all_new,
        )
