"""
Event representation module for temporal reasoning.
Defines the core Event data structure, timestamps, durations, and serialization.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any, Union


def parse_iso_datetime(val: Optional[Union[str, datetime]]) -> Optional[datetime]:
    """Parse ISO formatted datetime string or return datetime if already datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(val)


def parse_duration(val: Optional[Union[int, float, str, timedelta]]) -> Optional[timedelta]:
    """Parse duration as seconds (int/float), ISO/string, or return timedelta."""
    if val is None:
        return None
    if isinstance(val, timedelta):
        return val
    if isinstance(val, (int, float)):
        return timedelta(seconds=val)
    if isinstance(val, str):
        # Support string formats like "90m", "2h", or standard seconds
        val_lower = val.strip().lower()
        if val_lower.endswith("m") or val_lower.endswith("min") or val_lower.endswith("minutes"):
            num = float(val_lower.rstrip("minutse "))
            return timedelta(minutes=num)
        if val_lower.endswith("h") or val_lower.endswith("hr") or val_lower.endswith("hours"):
            num = float(val_lower.rstrip("hourse "))
            return timedelta(hours=num)
        if val_lower.endswith("d") or val_lower.endswith("days"):
            num = float(val_lower.rstrip("days "))
            return timedelta(days=num)
        if val_lower.endswith("s") or val_lower.endswith("sec") or val_lower.endswith("seconds"):
            num = float(val_lower.rstrip("seconde "))
            return timedelta(seconds=num)
        return timedelta(seconds=float(val))
    raise ValueError(f"Cannot parse duration from value: {val}")


@dataclass
class Event:
    """
    Representation of an event with temporal bounds and descriptions.

    Attributes:
        event_id: Unique identifier for the event (e.g. 'E1').
        description: Natural-language or symbolic description of the event.
        start_time: Optional start timestamp (datetime).
        end_time: Optional end timestamp (datetime).
        duration: Optional duration (timedelta).
    """

    event_id: str
    description: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None

    def __post_init__(self):
        self.start_time = parse_iso_datetime(self.start_time)
        self.end_time = parse_iso_datetime(self.end_time)
        self.duration = parse_duration(self.duration)
        if self.start_time and self.end_time and self.duration is None:
            self.duration = self.end_time - self.start_time
        self.validate()

    def validate(self) -> None:
        """Validate consistency of start, end, and duration bounds."""
        if self.start_time and self.end_time:
            if self.start_time > self.end_time:
                raise ValueError(
                    f"Event {self.event_id}: start_time ({self.start_time}) cannot be after end_time ({self.end_time})"
                )
            computed_duration = self.end_time - self.start_time
            if self.duration is not None and abs(self.duration.total_seconds() - computed_duration.total_seconds()) > 1e-3:
                raise ValueError(
                    f"Event {self.event_id}: explicit duration {self.duration} conflicts with end_time - start_time {computed_duration}"
                )
        if self.duration is not None and self.duration.total_seconds() < 0:
            raise ValueError(f"Event {self.event_id}: duration cannot be negative ({self.duration})")

    @property
    def is_instantaneous(self) -> bool:
        """True if the event has identical start and end time or zero duration."""
        if self.start_time and self.end_time and self.start_time == self.end_time:
            return True
        if self.duration and self.duration.total_seconds() == 0:
            return True
        return False

    @property
    def has_bounds(self) -> bool:
        """True if any temporal bound (start, end, or duration) is defined."""
        return bool(self.start_time or self.end_time or self.duration)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to JSON-serializable dictionary."""
        return {
            "event_id": self.event_id,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration.total_seconds() if self.duration else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        """Construct Event instance from a dictionary."""
        return cls(
            event_id=data["event_id"],
            description=data.get("description", ""),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            duration=data.get("duration"),
        )

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize event to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> Event:
        """Deserialize Event from JSON string."""
        return cls.from_dict(json.loads(json_str))
