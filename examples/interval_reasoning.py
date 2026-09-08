"""
Interval reasoning example.
Demonstrates start/end boundary deduction, duration resolution,
and automated derivation of Allen's interval relations.
"""

from datetime import datetime, timedelta
from temporal_reasoning import (
    TemporalReasoningEngine,
    Event,
    TemporalRelation,
    TemporalNormalizer,
)


def run_interval_reasoning():
    print("=== 1. Temporal Expression Normalization ===")
    anchor = datetime(2026, 9, 8, 9, 0, 0)
    normalizer = TemporalNormalizer(default_anchor=anchor)

    phrases = [
        "today",
        "two days ago",
        "for 90 minutes",
        "at 14:30",
        "on 12 March 2026",
    ]
    for p in phrases:
        norm = normalizer.normalize_text(p)
        print(f"Phrase: '{p}' -> {norm[0].to_dict()}")

    print("\n=== 2. Interval Bounds & Allen Relation Deduction ===")
    engine = TemporalReasoningEngine(anchor_date=anchor)

    # Event 1: Morning Workshop starts at 09:00 and lasts for 2 hours
    engine.add_statement("Morning Workshop started at 09:00. It lasted for 2 hours.")

    # Event 2: Lunch Break from 11:00 to 12:00
    lunch = Event(
        event_id="E_Lunch",
        description="Lunch Break",
        start_time=datetime(2026, 9, 8, 11, 0, 0),
        end_time=datetime(2026, 9, 8, 12, 0, 0),
    )
    engine.add_event(lunch)

    # Event 3: Keynote Talk from 11:30 to 12:30 (overlaps with Lunch)
    keynote = Event(
        event_id="E_Keynote",
        description="Keynote Talk",
        start_time=datetime(2026, 9, 8, 11, 30, 0),
        end_time=datetime(2026, 9, 8, 12, 30, 0),
    )
    engine.add_event(keynote)

    engine.run_inference()

    # Query relations between intervals
    rel_workshop_lunch = engine.query("Morning Workshop", "Lunch Break")
    rel_lunch_keynote = engine.query("Lunch Break", "Keynote Talk")

    print(f"Workshop vs Lunch:   {rel_workshop_lunch.value.upper() if rel_workshop_lunch else 'UNKNOWN'}")
    print(f"Lunch vs Keynote:    {rel_lunch_keynote.value.upper() if rel_lunch_keynote else 'UNKNOWN'}")

    workshop_ev = engine.graph.get_event("Morning Workshop")
    print(f"Workshop start:      {workshop_ev.start_time}")
    print(f"Workshop end:        {workshop_ev.end_time} (inferred via start + duration)")


if __name__ == "__main__":
    run_interval_reasoning()
