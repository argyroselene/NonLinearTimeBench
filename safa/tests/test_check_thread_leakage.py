import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from scripts.check_thread_leakage import (
    audit_story,
    name_opening_rate,
    thread_aliases,
    trivial_lexical_baseline_accuracy,
)


def test_thread_aliases_extracts_name_before_comma():
    assert thread_aliases("Tanner, on the beach") == {"Tanner"}


def test_thread_aliases_strips_title_stopwords():
    assert thread_aliases("Inspector Voss, present-day investigation") == {"Voss"}
    assert thread_aliases("Dr. Amara, ER shift") == {"Amara"}


def test_thread_aliases_returns_empty_for_role_only_label():
    assert thread_aliases("the crew, inside the bank") == set()


def test_thread_aliases_handles_slash_separated_names():
    assert thread_aliases("Nurse Boone / Ito, ICU shift") == {"Boone", "Ito"}


def _leaky_story():
    return {
        "threads": [
            {"id": "A", "label": "Farrow, in the air"},
            {"id": "L", "label": "Tanner, on the beach"},
        ],
        "events": [
            {"id": "s1", "thread_id": "A", "text": "Farrow scans the horizon."},
            {"id": "s2", "thread_id": "L", "text": "Tanner digs into the sand."},
            {"id": "s3", "thread_id": "A", "text": "Farrow banks hard left."},
            {"id": "s4", "thread_id": "L", "text": "Tanner watches the mole burn."},
        ],
    }


def _non_leaky_story():
    return {
        "threads": [
            {"id": "A", "label": "Farrow, in the air"},
            {"id": "L", "label": "Tanner, on the beach"},
        ],
        "events": [
            {"id": "s1", "thread_id": "A", "text": "The pilot scans the horizon, fuel low."},
            {"id": "s2", "thread_id": "L", "text": "He has been dug into the sand for days."},
            {"id": "s3", "thread_id": "A", "text": "He banks hard as a plane goes down."},
            {"id": "s4", "thread_id": "L", "text": "Someone calls out that Farrow's squadron flew over."},
        ],
    }


def test_name_opening_rate_is_one_when_every_event_opens_with_name():
    rates = name_opening_rate(_leaky_story())
    assert rates == {"A": 1.0, "L": 1.0}


def test_name_opening_rate_drops_when_names_are_not_used_to_open():
    rates = name_opening_rate(_non_leaky_story())
    assert rates == {"A": 0.0, "L": 0.0}


def test_trivial_lexical_baseline_scores_near_ceiling_on_leaky_story():
    accuracy = trivial_lexical_baseline_accuracy(_leaky_story())
    assert accuracy == 1.0


def test_trivial_lexical_baseline_is_hurt_by_cross_thread_distractor_mention():
    accuracy = trivial_lexical_baseline_accuracy(_non_leaky_story())
    assert accuracy < 1.0


def test_audit_story_flags_leaky_story_over_threshold():
    result = audit_story(_leaky_story())
    assert result["threads_over_threshold"] == {"A": 1.0, "L": 1.0}
    assert result["baseline_over_threshold"] is True


def test_audit_story_does_not_flag_non_leaky_story():
    result = audit_story(_non_leaky_story())
    assert result["threads_over_threshold"] == {}
