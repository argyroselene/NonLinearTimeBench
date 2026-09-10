"""
Natural-language temporal statement parser.
Extracts events, temporal bounds (start, end, duration), and temporal relations
from sentences, supporting coreference resolution and multi-sentence context.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from temporal_reasoning.events import Event
from temporal_reasoning.relations import TemporalRelation, parse_relation
from temporal_reasoning.expressions import extract_temporal_expressions
from temporal_reasoning.normalizer import TemporalNormalizer, NormalizedTemporalExpression


@dataclass
class ParsedStatement:
    """
    Structured outcome of parsing a natural language statement.

    Attributes:
        raw_text: The sentence or phrase parsed.
        statement_type: 'RELATION', 'EVENT_BOUND', or 'UNPARSED'.
        source_event: The primary or subject event.
        target_event: The secondary or object event (for relations).
        relation: Extracted TemporalRelation (if statement_type == 'RELATION').
        bound_type: 'start', 'end', or 'duration' (if statement_type == 'EVENT_BOUND').
        bound_value: datetime or timedelta.
    """

    raw_text: str
    statement_type: str
    source_event: Optional[Event] = None
    target_event: Optional[Event] = None
    relation: Optional[TemporalRelation] = None
    bound_type: Optional[str] = None
    bound_value: Optional[Union[datetime, timedelta]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "statement_type": self.statement_type,
            "source_event": self.source_event.to_dict() if self.source_event else None,
            "target_event": self.target_event.to_dict() if self.target_event else None,
            "relation": self.relation.value if self.relation else None,
            "bound_type": self.bound_type,
            "bound_value": (
                self.bound_value.isoformat()
                if isinstance(self.bound_value, datetime)
                else self.bound_value.total_seconds()
                if isinstance(self.bound_value, timedelta)
                else None
            ),
        }


class StatementParser:
    """Parses natural-language statements into events, bounds, and temporal relations."""

    def __init__(self, anchor_date: Optional[datetime] = None):
        self.normalizer = TemporalNormalizer(default_anchor=anchor_date)
        self.last_event: Optional[Event] = None
        self._event_registry: Dict[str, Event] = {}
        self._id_counter = 1

    def reset(self):
        """Reset parser context and event counter."""
        self.last_event = None
        self._event_registry.clear()
        self._id_counter = 1

    def _get_or_create_event(self, description: str) -> Event:
        clean_desc = description.strip().rstrip(".")
        if not clean_desc:
            clean_desc = f"Event_{self._id_counter}"
        
        # Check if already registered
        norm_key = clean_desc.lower()
        if norm_key in self._event_registry:
            return self._event_registry[norm_key]

        ev_id = f"E{self._id_counter}"
        self._id_counter += 1
        ev = Event(event_id=ev_id, description=clean_desc)
        self._event_registry[norm_key] = ev
        return ev

    def parse(self, text: str) -> List[ParsedStatement]:
        """Parse a paragraph or multi-sentence string into parsed statements."""
        # Split into sentences
        sentences = [s.strip() for s in re.split(r"[;\n.]+", text) if s.strip()]
        results: List[ParsedStatement] = []

        for sentence in sentences:
            parsed = self.parse_sentence(sentence)
            if parsed:
                results.append(parsed)

        return results

    def parse_sentence(self, sentence: str) -> ParsedStatement:
        """Parse a single sentence."""
        s = sentence.strip()

        # 1. Check for bound statements on existing/referred event:
        # e.g., "It lasted for 90 minutes." or "The meeting lasted for 90 minutes."
        duration_match = re.search(
            r"^(it|the\s+meeting|the\s+event|[A-Za-z0-9_'\s]+?)\s+(?:lasted|lasted\s+for|took|ran\s+for)\s+(.+)$",
            s,
            re.IGNORECASE,
        )
        if duration_match:
            subject_str = duration_match.group(1).strip()
            rest = duration_match.group(2).strip()
            ev = self._resolve_subject(subject_str)
            norm_exprs = self.normalizer.normalize_text(rest)
            dur_expr = next((ne for ne in norm_exprs if ne.resolved_duration is not None), None)
            if dur_expr and dur_expr.resolved_duration:
                ev.duration = dur_expr.resolved_duration
                self.last_event = ev
                return ParsedStatement(
                    raw_text=s,
                    statement_type="EVENT_BOUND",
                    source_event=ev,
                    bound_type="duration",
                    bound_value=dur_expr.resolved_duration,
                )

        # 2. Check for start time:
        # e.g., "The meeting started at 10:00" or "Alice arrived at 10:00"
        # 2. Check for start time or event occurrence:
        # e.g., "The meeting started at 10:00", "Alice arrived at 10:00", "MeetingA happened 2 days ago"
        start_match = re.search(
            r"^(.*?)\s+(?:started|began|commenced|arrived|happened|occurred)\s+(?:at|on|in)?\s*(.+)$",
            s,
            re.IGNORECASE,
        )
        if start_match:
            subject_str = start_match.group(1).strip()
            rest = start_match.group(2).strip()
            ev = self._resolve_subject(subject_str)
            norm_exprs = self.normalizer.normalize_text(rest)
            time_expr = next((ne for ne in norm_exprs if ne.resolved_datetime is not None), None)
            if time_expr and time_expr.resolved_datetime:
                ev.start_time = time_expr.resolved_datetime
                self.last_event = ev
                return ParsedStatement(
                    raw_text=s,
                    statement_type="EVENT_BOUND",
                    source_event=ev,
                    bound_type="start",
                    bound_value=time_expr.resolved_datetime,
                )

        # 3. Check for end time:
        # e.g., "The meeting ended at 11:30" or "Bob left at 11:00"
        end_match = re.search(
            r"^(.*?)\s+(?:ended|finished|adjourned|concluded|left)\s+(?:at|on)\s+(.+)$",
            s,
            re.IGNORECASE,
        )
        if end_match:
            subject_str = end_match.group(1).strip()
            rest = end_match.group(2).strip()
            ev = self._resolve_subject(subject_str)
            norm_exprs = self.normalizer.normalize_text(rest)
            time_expr = next((ne for ne in norm_exprs if ne.resolved_datetime is not None), None)
            if time_expr and time_expr.resolved_datetime:
                ev.end_time = time_expr.resolved_datetime
                self.last_event = ev
                return ParsedStatement(
                    raw_text=s,
                    statement_type="EVENT_BOUND",
                    source_event=ev,
                    bound_type="end",
                    bound_value=time_expr.resolved_datetime,
                )

        # 4. Check for relational statements:
        relation_patterns = [
            (
                r"^(.*?)\s+(?:happened|occurred|arrived|left|took\s+place)?\s*(?:is\s+)?before\s+(.*?)$",
                TemporalRelation.BEFORE,
            ),
            (
                r"^(.*?)\s+(?:happened|occurred|arrived|left|took\s+place)?\s*(?:is\s+)?after\s+(.*?)$",
                TemporalRelation.AFTER,
            ),
            (
                r"^(.*?)\s+(?:happened|occurred)?\s*(?:is\s+)?during\s+(.*?)$",
                TemporalRelation.DURING,
            ),
            (
                r"^(.*?)\s+(?:meets|met)\s+(.*?)$",
                TemporalRelation.MEETS,
            ),
            (
                r"^(.*?)\s+(?:contains|contained|includes)\s+(.*?)$",
                TemporalRelation.CONTAINS,
            ),
            (
                r"^(.*?)\s+(?:starts|started)\s+(.*?)$",
                TemporalRelation.STARTS,
            ),
            (
                r"^(.*?)\s+(?:finishes|finished)\s+(.*?)$",
                TemporalRelation.FINISHES,
            ),
            (
                r"^(.*?)\s+(?:happened\s+at\s+the\s+same\s+time\s+as|is\s+equal\s+to|equals|equal|at\s+the\s+same\s+time\s+as)\s+(.*?)$",
                TemporalRelation.EQUAL,
            ),
        ]

        for pattern, rel in relation_patterns:
            m = re.search(pattern, s, re.IGNORECASE)
            if m:
                subj = m.group(1).strip()
                obj = m.group(2).strip()
                if subj and obj:
                    ev1 = self._get_or_create_event(self._clean_entity(subj))
                    ev2 = self._get_or_create_event(self._clean_entity(obj))
                    self.last_event = ev2
                    return ParsedStatement(
                        raw_text=s,
                        statement_type="RELATION",
                        source_event=ev1,
                        target_event=ev2,
                        relation=rel,
                    )

        # Fallback: create standalone event if not recognized
        ev = self._get_or_create_event(s)
        self.last_event = ev
        return ParsedStatement(
            raw_text=s,
            statement_type="UNPARSED",
            source_event=ev,
        )

    def _clean_entity(self, text: str) -> str:
        """Strip filler verbs from entity name."""
        t = re.sub(
            r"\b(arrived|left|started|ended|happened|occurred|departed)\b",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        return t if t else text

    def _resolve_subject(self, subj: str) -> Event:
        """Resolve pronoun or entity string to Event."""
        if subj.lower() in ("it", "the event", "this event") and self.last_event:
            return self.last_event
        return self._get_or_create_event(subj)
