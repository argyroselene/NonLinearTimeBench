"""Tests for temporal expression extraction."""

from temporal_reasoning.expressions import extract_temporal_expressions


def test_extract_named_relative_days():
    text = "Today is great, but yesterday was windy, and tomorrow will be sunny."
    exprs = extract_temporal_expressions(text)
    names = [e.metadata.get("named") for e in exprs if e.expr_type == "RELATIVE_DATE"]
    assert "today" in names
    assert "yesterday" in names
    assert "tomorrow" in names


def test_extract_offset_relative_dates():
    text = "The package arrived two days ago and another arrives three weeks later."
    exprs = extract_temporal_expressions(text)
    assert len(exprs) == 2
    assert exprs[0].expr_type == "RELATIVE_DATE"
    assert exprs[0].metadata["value"] == 2
    assert exprs[0].metadata["unit"] == "day"
    assert exprs[0].metadata["direction"] == "past"

    assert exprs[1].expr_type == "RELATIVE_DATE"
    assert exprs[1].metadata["value"] == 3
    assert exprs[1].metadata["unit"] == "week"
    assert exprs[1].metadata["direction"] == "future"


def test_extract_clock_times():
    text = "The meeting started at 10:30 and adjourned at 2:15 pm."
    exprs = extract_temporal_expressions(text)
    time_exprs = [e for e in exprs if e.expr_type == "TIME"]
    assert len(time_exprs) == 2
    assert time_exprs[0].metadata["hour"] == 10
    assert time_exprs[0].metadata["minute"] == 30
    assert time_exprs[1].metadata["hour"] == 14
    assert time_exprs[1].metadata["minute"] == 15


def test_extract_absolute_dates():
    text = "He was born on 12 March 2026 and graduated on 2026-09-10."
    exprs = extract_temporal_expressions(text)
    date_exprs = [e for e in exprs if e.expr_type == "ABSOLUTE_DATE"]
    assert len(date_exprs) == 2
    assert date_exprs[0].metadata["day"] == 12
    assert date_exprs[0].metadata["month"] == 3
    assert date_exprs[0].metadata["year"] == 2026

    assert date_exprs[1].metadata["year"] == 2026
    assert date_exprs[1].metadata["month"] == 9
    assert date_exprs[1].metadata["day"] == 10


def test_extract_durations():
    text = "The presentation lasted for 90 minutes, followed by a break for two hours."
    exprs = extract_temporal_expressions(text)
    durations = [e for e in exprs if e.expr_type == "DURATION"]
    assert len(durations) == 2
    assert durations[0].metadata["value"] == 90
    assert durations[0].metadata["unit"] == "minute"
    assert durations[1].metadata["value"] == 2
    assert durations[1].metadata["unit"] == "hour"


def test_extract_dow():
    text = "See you next Friday or last Monday."
    exprs = extract_temporal_expressions(text)
    dows = [e for e in exprs if "weekday" in e.metadata]
    assert len(dows) == 2
    assert dows[0].metadata["weekday"] == "friday"
    assert dows[0].metadata["modifier"] == "next"
    assert dows[1].metadata["weekday"] == "monday"
    assert dows[1].metadata["modifier"] == "last"
