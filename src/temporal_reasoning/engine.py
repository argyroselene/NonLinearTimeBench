"""
Unified Temporal Reasoning Engine.
Coordinates parsing, graph construction, symbolic inference, and queries.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from temporal_reasoning.events import Event
from temporal_reasoning.relations import TemporalRelation, parse_relation
from temporal_reasoning.graph import TemporalGraph, TemporalEdge
from temporal_reasoning.parser import StatementParser, ParsedStatement
from temporal_reasoning.inference import InferenceEngine, InferenceResult
from temporal_reasoning.consistency import ConsistencyChecker, TemporalConflict


class TemporalReasoningEngine:
    """
    High-level engine for temporal reasoning over natural language statements.

    Usage:
        engine = TemporalReasoningEngine()
        engine.add_statement("Alice arrived before Bob.")
        engine.add_statement("Bob left before Charlie.")
        relation = engine.query("Alice", "Charlie")
        # Returns TemporalRelation.BEFORE
    """

    def __init__(
        self,
        anchor_date: Optional[datetime] = None,
        auto_infer: bool = True,
    ):
        self.anchor_date = anchor_date
        self.auto_infer = auto_infer
        self.graph = TemporalGraph()
        self.parser = StatementParser(anchor_date=anchor_date)
        self.inference = InferenceEngine()
        self.checker = ConsistencyChecker()

    def reset(self) -> None:
        """Clear all events, graph state, and parser history."""
        self.graph = TemporalGraph()
        self.parser.reset()

    def add_statement(self, text: str) -> List[ParsedStatement]:
        """
        Parse natural-language statement(s), update graph, and trigger inference.
        """
        parsed_list = self.parser.parse(text)
        for stmt in parsed_list:
            if stmt.statement_type == "RELATION" and stmt.source_event and stmt.target_event and stmt.relation:
                self.graph.add_event(stmt.source_event)
                self.graph.add_event(stmt.target_event)
                self.graph.add_relation(
                    stmt.source_event,
                    stmt.target_event,
                    stmt.relation,
                    is_inferred=False,
                    provenance=f"Explicit statement: '{stmt.raw_text}'",
                )
            elif stmt.statement_type == "EVENT_BOUND" and stmt.source_event:
                self.graph.add_event(stmt.source_event)

        if self.auto_infer:
            self.run_inference()

        return parsed_list

    def add_event(self, event: Event) -> None:
        """Directly add an event to the reasoning graph."""
        self.graph.add_event(event)

    def add_relation(
        self,
        source: Union[str, Event],
        target: Union[str, Event],
        relation: Union[TemporalRelation, str],
        is_inferred: bool = False,
    ) -> TemporalEdge:
        """Directly add a relation edge to the graph."""
        rel_enum = parse_relation(relation)
        edge = self.graph.add_relation(source, target, rel_enum, is_inferred=is_inferred)
        if self.auto_infer:
            self.run_inference()
        return edge

    def run_inference(self) -> InferenceResult:
        """Run symbolic inference rules to completion on current graph."""
        return self.inference.run(self.graph)

    def query(
        self,
        source: Union[str, Event],
        target: Union[str, Event],
    ) -> Optional[TemporalRelation]:
        """
        Query the temporal relation between source and target events.
        Resolves event names, IDs, and performs inference if necessary.
        """
        # Run inference if not auto-inferred
        if not self.auto_infer:
            self.run_inference()

        src_id = self.graph._resolve_id(source)
        tgt_id = self.graph._resolve_id(target)

        # 1. Direct or previously inferred edge
        rel = self.graph.get_relation(src_id, tgt_id)
        if rel:
            return rel

        # 2. Run an extra inference pass if not found
        self.run_inference()
        rel = self.graph.get_relation(src_id, tgt_id)
        if rel:
            return rel

        # 3. Path-based deduction
        path = self.graph.find_path(src_id, tgt_id)
        if path:
            # Check if all edges are BEFORE
            if all(e.relation == TemporalRelation.BEFORE for e in path):
                return TemporalRelation.BEFORE
            if all(e.relation == TemporalRelation.AFTER for e in path):
                return TemporalRelation.AFTER

        return None

    def query_explanation(
        self,
        source: Union[str, Event],
        target: Union[str, Event],
    ) -> Optional[str]:
        """Return the reasoning explanation / provenance for a relation."""
        src_id = self.graph._resolve_id(source)
        tgt_id = self.graph._resolve_id(target)
        edges = self.graph._adjacency.get(src_id, {}).get(tgt_id, [])
        if edges:
            return edges[0].provenance
        return None

    def check_consistency(self) -> List[TemporalConflict]:
        """Inspect the current graph for temporal contradictions."""
        return self.checker.check(self.graph)

    def is_consistent(self) -> bool:
        """Return True if the graph is consistent."""
        return self.checker.is_consistent(self.graph)
