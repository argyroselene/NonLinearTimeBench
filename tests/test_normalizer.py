"""Tests for temporal expression normalization."""

from datetime import datetime, timedelta
from temporal_reasoning.expressions import extract_temporal_expressions
from temporal_reasoning.normalizer import TemporalNormalizer, normalize_text


def test_normalize_absolute_date():
    text = "The launch occurred on 12 March 2026."
    normalized = normalize_text(text)
    assert len(normalized) == 1
    norm = normalized[0]
    assert norm.type == "ABSOLUTE_DATE"
    assert norm.resolved_datetime == datetime(2026, 3, 12, 0, 0, 0)


def test_normalize_time():
    anchor = datetime(2026, 8, 10, 0, 0, 0)
    normalizer = TemporalNormalizer(default_anchor=anchor)
    text = "Meeting at 14:30."
    normalized = normalizer.normalize_text(text)
    assert len(normalized) == 1
    norm = normalized[0]
    assert norm.type == "TIME"
    assert norm.resolved_datetime == datetime(2026, 8, 10, 14, 30, 0)


def test_normalize_relative_offset():
    anchor = datetime(2026, 8, 10, 12, 0, 0)
    normalizer = TemporalNormalizer(default_anchor=anchor)

    # 2 days ago
    res_ago = normalizer.normalize_text("Finished two days ago.")[0]
    assert res_ago.type == "RELATIVE_DATE"
    assert res_ago.value == 2
    assert res_ago.unit == "day"
    assert res_ago.direction == "past"
    assert res_ago.resolved_datetime == datetime(2026, 8, 8, 12, 0, 0)

    # 3 weeks later
    res_later = normalizer.normalize_text("Release scheduled three weeks later.")[0]
    assert res_later.direction == "future"
    assert res_later.resolved_datetime == anchor + timedelta(weeks=3)


def test_normalize_named_relative():
    anchor = datetime(2026, 8, 10, 10, 0, 0)
    normalizer = TemporalNormalizer(default_anchor=anchor)

    res_yesterday = normalizer.normalize_text("We met yesterday.")[0]
    assert res_yesterday.resolved_datetime == datetime(2026, 8, 9, 10, 0, 0)

    res_tomorrow = normalizer.normalize_text("We meet tomorrow.")[0]
    assert res_tomorrow.resolved_datetime == datetime(2026, 8, 11, 10, 0, 0)


def test_normalize_duration():
    text = "The exam lasted for 90 minutes."
    normalized = normalize_text(text)
    assert len(normalized) == 1
    norm = normalized[0]
    assert norm.type == "DURATION"
    assert norm.value == 90
    assert norm.unit == "minute"
    assert norm.resolved_duration == timedelta(minutes=90)
