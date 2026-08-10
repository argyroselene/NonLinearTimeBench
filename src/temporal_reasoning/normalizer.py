"""
Temporal expression normalization module.
Normalizes extracted expressions into structured representations and resolves
relative references against reference/anchor datetimes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import Any, Dict, List, Optional, Union

from temporal_reasoning.expressions import TemporalExpression, extract_temporal_expressions, WEEKDAYS


@dataclass
class NormalizedTemporalExpression:
    """
    Standardized, structured temporal expression.

    Attributes:
        text: Original substring.
        type: Expression category ('RELATIVE_DATE', 'ABSOLUTE_DATE', 'TIME', 'DURATION').
        value: Numeric value if applicable (e.g. 2 for "two days later").
        unit: Temporal unit ('second', 'minute', 'hour', 'day', 'week', 'month', 'year').
        direction: Direction ('past', 'future', 'current') if applicable.
        resolved_datetime: Concrete datetime resolved against anchor date if applicable.
        resolved_duration: Concrete timedelta if duration or offset.
    """

    text: str
    type: str
    value: Optional[Union[int, float]] = None
    unit: Optional[str] = None
    direction: Optional[str] = None
    resolved_datetime: Optional[datetime] = None
    resolved_duration: Optional[timedelta] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "text": self.text,
            "type": self.type,
        }
        if self.value is not None:
            res["value"] = self.value
        if self.unit is not None:
            res["unit"] = self.unit
        if self.direction is not None:
            res["direction"] = self.direction
        if self.resolved_datetime is not None:
            res["resolved_datetime"] = self.resolved_datetime.isoformat()
        if self.resolved_duration is not None:
            res["resolved_duration_seconds"] = self.resolved_duration.total_seconds()
        if self.extra:
            res["extra"] = self.extra
        return res


class TemporalNormalizer:
    """Normalizes extracted expressions into structured representations and concrete datetimes."""

    def __init__(self, default_anchor: Optional[datetime] = None):
        self.default_anchor = default_anchor or datetime(2026, 9, 13, 0, 0, 0)

    def normalize(
        self,
        expr: TemporalExpression,
        anchor: Optional[datetime] = None,
    ) -> NormalizedTemporalExpression:
        """Normalize a single TemporalExpression."""
        ref = anchor or self.default_anchor
        meta = expr.metadata

        if expr.expr_type == "ABSOLUTE_DATE":
            year = meta.get("year", ref.year)
            month = meta["month"]
            day = meta["day"]
            resolved = datetime(year, month, day)
            return NormalizedTemporalExpression(
                text=expr.raw_text,
                type="ABSOLUTE_DATE",
                resolved_datetime=resolved,
                extra={"year": year, "month": month, "day": day},
            )

        elif expr.expr_type == "TIME":
            h = meta["hour"]
            m = meta["minute"]
            s = meta.get("second", 0)
            resolved = datetime(ref.year, ref.month, ref.day, h, m, s)
            return NormalizedTemporalExpression(
                text=expr.raw_text,
                type="TIME",
                resolved_datetime=resolved,
                extra={"hour": h, "minute": m, "second": s},
            )

        elif expr.expr_type == "DURATION":
            val = meta["value"]
            unit = meta["unit"]
            delta = self._unit_to_timedelta(val, unit)
            return NormalizedTemporalExpression(
                text=expr.raw_text,
                type="DURATION",
                value=val,
                unit=unit,
                resolved_duration=delta,
            )

        elif expr.expr_type == "RELATIVE_DATE":
            # Check if it is a named relative day (today, yesterday, tomorrow)
            if "named" in meta:
                named = meta["named"]
                offset_days = meta["offset_days"]
                resolved = ref + timedelta(days=offset_days)
                return NormalizedTemporalExpression(
                    text=expr.raw_text,
                    type="RELATIVE_DATE",
                    value=meta["value"],
                    unit="day",
                    direction=meta["direction"],
                    resolved_datetime=resolved,
                    resolved_duration=timedelta(days=offset_days),
                    extra={"named": named},
                )

            # Check if it is an offset relative date ("two days ago", "3 weeks later")
            elif "value" in meta and "unit" in meta and "direction" in meta:
                val = meta["value"]
                unit = meta["unit"]
                direction = meta["direction"]
                delta = self._unit_to_timedelta(val, unit)
                if direction == "past":
                    resolved = ref - delta
                    signed_duration = -delta
                else:
                    resolved = ref + delta
                    signed_duration = delta

                return NormalizedTemporalExpression(
                    text=expr.raw_text,
                    type="RELATIVE_DATE",
                    value=val,
                    unit=unit,
                    direction=direction,
                    resolved_datetime=resolved,
                    resolved_duration=signed_duration,
                )

            # Check if it is a day of week ("next Friday", "last Monday")
            elif "weekday" in meta and "modifier" in meta:
                target_wd = WEEKDAYS.index(meta["weekday"])
                modifier = meta["modifier"]
                cur_wd = ref.weekday()

                if modifier == "next":
                    diff = (target_wd - cur_wd) % 7
                    if diff == 0:
                        diff = 7
                elif modifier == "last":
                    diff = (cur_wd - target_wd) % 7
                    if diff == 0:
                        diff = 7
                    diff = -diff
                else:  # "this"
                    diff = (target_wd - cur_wd)

                resolved = ref + timedelta(days=diff)
                return NormalizedTemporalExpression(
                    text=expr.raw_text,
                    type="RELATIVE_DATE",
                    unit="day",
                    direction="future" if diff > 0 else "past" if diff < 0 else "current",
                    resolved_datetime=resolved,
                    resolved_duration=timedelta(days=diff),
                    extra={"modifier": modifier, "weekday": meta["weekday"]},
                )

        # Fallback
        return NormalizedTemporalExpression(
            text=expr.raw_text,
            type=expr.expr_type,
            extra=meta,
        )

    def normalize_text(
        self,
        text: str,
        anchor: Optional[datetime] = None,
    ) -> List[NormalizedTemporalExpression]:
        """Extract and normalize all temporal expressions in text."""
        exprs = extract_temporal_expressions(text)
        return [self.normalize(e, anchor=anchor) for e in exprs]

    @staticmethod
    def _unit_to_timedelta(val: Union[int, float], unit: str) -> timedelta:
        unit = unit.lower().rstrip("s")
        if unit == "second":
            return timedelta(seconds=val)
        if unit == "minute":
            return timedelta(minutes=val)
        if unit == "hour":
            return timedelta(hours=val)
        if unit == "day":
            return timedelta(days=val)
        if unit == "week":
            return timedelta(weeks=val)
        if unit == "month":
            # Approximate 30 days
            return timedelta(days=int(val * 30))
        if unit == "year":
            # Approximate 365 days
            return timedelta(days=int(val * 365))
        return timedelta(seconds=val)


_default_normalizer = TemporalNormalizer()


def normalize_expression(
    expr: TemporalExpression,
    anchor: Optional[datetime] = None,
) -> NormalizedTemporalExpression:
    """Normalize a temporal expression using default normalizer."""
    return _default_normalizer.normalize(expr, anchor=anchor)


def normalize_text(
    text: str,
    anchor: Optional[datetime] = None,
) -> List[NormalizedTemporalExpression]:
    """Extract and normalize all temporal expressions in text."""
    return _default_normalizer.normalize_text(text, anchor=anchor)
