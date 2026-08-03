"""Tests for the Event data model."""

import pytest
from datetime import datetime, timedelta
from temporal_reasoning.events import Event


def test_event_initialization_minimal():
    ev = Event(event_id="E1", description="Alice arrived")
    assert ev.event_id == "E1"
    assert ev.description == "Alice arrived"
    assert ev.start_time is None
    assert ev.end_time is None
    assert ev.duration is None
    assert not ev.has_bounds
    assert not ev.is_instantaneous


def test_event_initialization_full():
    start = datetime(2026, 9, 10, 9, 0, 0)
    end = datetime(2026, 9, 10, 10, 30, 0)
    dur = timedelta(minutes=90)
    ev = Event(
        event_id="E2",
        description="Morning meeting",
        start_time=start,
        end_time=end,
        duration=dur,
    )
    assert ev.has_bounds
    assert not ev.is_instantaneous
    assert ev.duration.total_seconds() == 5400


def test_event_serialization_and_deserialization():
    start_str = "2026-09-10T09:00:00"
    end_str = "2026-09-10T10:30:00"
    ev = Event(
        event_id="E1",
        description="Alice arrived",
        start_time=start_str,
        end_time=end_str,
        duration=5400,
    )
    data = ev.to_dict()
    assert data["event_id"] == "E1"
    assert data["start_time"] == start_str
    assert data["duration"] == 5400.0

    ev2 = Event.from_dict(data)
    assert ev2.event_id == ev.event_id
    assert ev2.start_time == ev.start_time
    assert ev2.end_time == ev.end_time
    assert ev2.duration == ev.duration

    json_str = ev.to_json()
    ev3 = Event.from_json(json_str)
    assert ev3.event_id == ev.event_id


def test_event_invalid_timestamps():
    with pytest.raises(ValueError, match="cannot be after end_time"):
        Event(
            event_id="E_invalid",
            description="Time traveler",
            start_time="2026-09-10T12:00:00",
            end_time="2026-09-10T10:00:00",
        )


def test_event_invalid_duration_conflict():
    with pytest.raises(ValueError, match="conflicts with"):
        Event(
            event_id="E_conflict",
            description="Conflicting duration",
            start_time="2026-09-10T10:00:00",
            end_time="2026-09-10T11:00:00",
            duration=7200,  # 2 hours instead of 1 hour
        )
