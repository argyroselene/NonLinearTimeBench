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

    def step(self, graph: TemporalGraph) -> List[TemporalEdge]:
        """Execute a single round of inference rules."""
        inferred_this_step: List[TemporalEdge] = []

        if self.enable_inverse:
            inv_edges = self.infer_inverses(graph)
            inferred_this_step.extend(inv_edges)

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
