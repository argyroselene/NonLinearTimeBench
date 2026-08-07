"""
Temporal expression extraction module.
Identifies and extracts time, date, duration, and relative temporal mentions
from natural-language text using robust regular expressions and rule patterns.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional


@dataclass
class TemporalExpression:
    """
    Extracted temporal expression with span and classification.

    Attributes:
        raw_text: Substring matching the expression.
        expr_type: Category ('RELATIVE_DATE', 'ABSOLUTE_DATE', 'TIME', 'DURATION', 'TEMPORAL_MARKER').
        start_char: Start character index in the source text.
        end_char: End character index in the source text.
        metadata: Extracted components (e.g. quantity, unit, direction).
    """

    raw_text: str
    expr_type: str
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "expr_type": self.expr_type,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata,
        }


# Word to number conversion helper for small numerals
WORD_TO_NUM: Dict[str, int] = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

MONTH_MAP: Dict[str, int] = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

WEEKDAYS: List[str] = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]


NUM_PATTERN = r"(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten)"
UNIT_PATTERN = r"(?:second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)"
DIR_PATTERN = r"(?:ago|earlier|before|later|after)"


class TemporalExpressionExtractor:
    """Rule-based extractor for temporal expressions in natural language."""

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        # 1. Named relative days: today, yesterday, tomorrow
        self.re_named_relative = re.compile(
            r"\b(today|yesterday|tomorrow)\b",
            re.IGNORECASE,
        )

        # 2. Offset relative dates: e.g. "two days ago", "3 weeks later", "5 minutes earlier"
        self.re_offset_relative = re.compile(
            rf"\b({NUM_PATTERN})\s+({UNIT_PATTERN})\s+({DIR_PATTERN})\b",
            re.IGNORECASE,
        )

        # 3. Day of week expressions: "last Monday", "next Friday", "this Tuesday"
        days_regex = "|".join(WEEKDAYS)
        self.re_dow = re.compile(
            rf"\b(last|next|this)\s+({days_regex})\b",
            re.IGNORECASE,
        )

        # 4. Durations: "for two hours", "for 90 minutes", "lasted 3 days"
        self.re_duration = re.compile(
            rf"\b(?:for|lasted\s+(?:for\s+)?|lasting\s+|duration\s+of\s+)({NUM_PATTERN})\s+({UNIT_PATTERN})\b",
            re.IGNORECASE,
        )

        # 5. Clock times: "at 10:30", "10:00", "11:30 am", "2:15 pm"
        self.re_time = re.compile(
            r"\b(?:at\s+)?([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?\s*(am|pm)?\b",
            re.IGNORECASE,
        )

        # 6. Absolute dates: "12 March 2026", "March 12, 2026", "2026-09-10"
        months_regex = "|".join(MONTH_MAP.keys())
        self.re_iso_date = re.compile(
            r"\b(\d{4})-(\d{2})-(\d{2})\b"
        )
        self.re_written_date_1 = re.compile(
            rf"\b(?:on\s+)?(\d{{1,2}})(?:st|nd|rd|th)?\s+({months_regex})\s+(\d{{4}})\b",
            re.IGNORECASE,
        )
        self.re_written_date_2 = re.compile(
            rf"\b(?:on\s+)?({months_regex})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?\b",
            re.IGNORECASE,
        )

    def extract(self, text: str) -> List[TemporalExpression]:
        """Extract all temporal expressions from text, sorted by character position."""
        expressions: List[TemporalExpression] = []
        covered_spans: List[tuple[int, int]] = []

        def spans_overlap(start: int, end: int) -> bool:
            for s, e in covered_spans:
                if max(start, s) < min(end, e):
                    return True
            return False

        # Priority 1: ISO Dates
        for m in self.re_iso_date.finditer(text):
            s, e = m.span()
            if not spans_overlap(s, e):
                covered_spans.append((s, e))
                expressions.append(
                    TemporalExpression(
                        raw_text=m.group(0),
                        expr_type="ABSOLUTE_DATE",
                        start_char=s,
                        end_char=e,
                        metadata={
                            "year": int(m.group(1)),
                            "month": int(m.group(2)),
                            "day": int(m.group(3)),
                        },
                    )
                )

        # Priority 2: Written Dates
        for m in self.re_written_date_1.finditer(text):
            s, e = m.span()
            if not spans_overlap(s, e):
                covered_spans.append((s, e))
                expressions.append(
                    TemporalExpression(
                        raw_text=m.group(0),
                        expr_type="ABSOLUTE_DATE",
                        start_char=s,
                        end_char=e,
                        metadata={
                            "day": int(m.group(1)),
                            "month": MONTH_MAP[m.group(2).lower()],
                            "year": int(m.group(3)),
                        },
                    )
                )

        for m in self.re_written_date_2.finditer(text):
            s, e = m.span()
            if not spans_overlap(s, e):
                covered_spans.append((s, e))
                expressions.append(
                    TemporalExpression(
                        raw_text=m.group(0),
                        expr_type="ABSOLUTE_DATE",
                        start_char=s,
                        end_char=e,
                        metadata={
                            "month": MONTH_MAP[m.group(1).lower()],
                            "day": int(m.group(2)),
                            "year": int(m.group(3)) if m.group(3) else None,
                        },
                    )
                )

        # Priority 3: Clock Times
        for m in self.re_time.finditer(text):
            s, e = m.span()
            if not spans_overlap(s, e):
                covered_spans.append((s, e))
                hour = int(m.group(1))
                minute = int(m.group(2))
                second = int(m.group(3)) if m.group(3) else 0
                meridiem = m.group(4).lower() if m.group(4) else None
                if meridiem == "pm" and hour < 12:
                    hour += 12
                elif meridiem == "am" and hour == 12:
                    hour = 0
                expressions.append(
                    TemporalExpression(
                        raw_text=m.group(0),
                        expr_type="TIME",
                        start_char=s,
                        end_char=e,
                        metadata={"hour": hour, "minute": minute, "second": second},
                    )
                )

        # Priority 4: Offset Relative Dates ("two days ago", "3 weeks later")
        for m in self.re_offset_relative.finditer(text):
            s, e = m.span()
            if not spans_overlap(s, e):
                covered_spans.append((s, e))
                qty_raw = m.group(1).lower()
                qty = WORD_TO_NUM.get(qty_raw, int(qty_raw) if qty_raw.isdigit() else 1)
                unit = m.group(2).lower().rstrip("s")
                direction = "past" if m.group(3).lower() in ("ago", "earlier", "before") else "future"
                expressions.append(
                    TemporalExpression(
                        raw_text=m.group(0),
                        expr_type="RELATIVE_DATE",
                        start_char=s,
                        end_char=e,
                        metadata={
                            "value": qty,
                            "unit": unit,
                            "direction": direction,
                        },
                    )
                )

        # Priority 5: Named Relative Dates ("today", "yesterday", "tomorrow")
        for m in self.re_named_relative.finditer(text):
            s, e = m.span()
            if not spans_overlap(s, e):
                covered_spans.append((s, e))
                val = m.group(1).lower()
                offset_days = {"today": 0, "yesterday": -1, "tomorrow": 1}[val]
                expressions.append(
                    TemporalExpression(
                        raw_text=m.group(0),
                        expr_type="RELATIVE_DATE",
                        start_char=s,
                        end_char=e,
                        metadata={
                            "named": val,
                            "offset_days": offset_days,
                            "value": abs(offset_days),
                            "unit": "day",
                            "direction": "past" if offset_days < 0 else "future" if offset_days > 0 else "current",
                        },
                    )
                )

        # Priority 6: Day of Week ("last Monday", "next Friday")
        for m in self.re_dow.finditer(text):
            s, e = m.span()
            if not spans_overlap(s, e):
                covered_spans.append((s, e))
                expressions.append(
                    TemporalExpression(
                        raw_text=m.group(0),
                        expr_type="RELATIVE_DATE",
                        start_char=s,
                        end_char=e,
                        metadata={
                            "modifier": m.group(1).lower(),
                            "weekday": m.group(2).lower(),
                        },
                    )
                )

        # Priority 7: Durations ("for two hours", "lasted for 90 minutes")
        # Match only when preceded by duration cues or isolated unit
        duration_cues = re.compile(
            rf"\b(?:for|lasted\s+(?:for\s+)?|lasting|duration\s+of)\s+({NUM_PATTERN})\s+({UNIT_PATTERN})\b",
            re.IGNORECASE,
        )
        for m in duration_cues.finditer(text):
            s, e = m.span()
            if not spans_overlap(s, e):
                covered_spans.append((s, e))
                qty_raw = m.group(1).lower()
                qty = WORD_TO_NUM.get(qty_raw, int(qty_raw) if qty_raw.isdigit() else 1)
                unit = m.group(2).lower().rstrip("s")
                expressions.append(
                    TemporalExpression(
                        raw_text=m.group(0),
                        expr_type="DURATION",
                        start_char=s,
                        end_char=e,
                        metadata={"value": qty, "unit": unit},
                    )
                )

        expressions.sort(key=lambda x: x.start_char)
        return expressions


# Convenience function
_default_extractor = TemporalExpressionExtractor()


def extract_temporal_expressions(text: str) -> List[TemporalExpression]:
    """Extract temporal expressions from text using the default extractor."""
    return _default_extractor.extract(text)
