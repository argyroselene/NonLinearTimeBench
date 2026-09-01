"""Thread-attribution leakage audit (docs/hypothesis_expansion_and_leakage_remediation_plan.md, Part 2.2).

Measures, per story, whether a thread's identity can be recovered from
surface name-matching alone rather than genuine narrative-structure
reasoning. Two checks, both zero-LLM and deterministic:

1. Name-opening rate: the fraction of a thread's events whose text opens
   (within the first `OPENING_WINDOW` words) with one of that thread's
   character-name aliases, derived heuristically from the thread's `label`
   field (e.g. "Inspector Voss, present-day investigation" -> alias "Voss").
2. Trivial lexical-baseline accuracy: a classifier with no semantic
   reasoning at all -- it predicts each event's thread purely by which
   thread's alias set appears anywhere in the event text -- scored with the
   same `thread_attribution_accuracy` used by AWT-F1
   (metrics/awt_f1.py). If this trivial baseline already scores near
   ceiling, the sub-metric cannot be distinguishing real reasoning from
   name lookup, regardless of what an LLM scores.

This is a diagnostic/authoring-integrity tool (same category as
scripts/check_coverage.py), not part of the scored pipeline.
"""

import json
import os
import re
import sys
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from metrics.awt_f1 import thread_attribution_accuracy

STORIES_DIR = os.path.join(ROOT, "data", "stories")

OPENING_WINDOW = 4
NAME_OPENING_RATE_THRESHOLD = 0.40
TRIVIAL_BASELINE_ACCURACY_THRESHOLD = 0.85

_TITLE_STOPWORDS = {
    "The", "A", "An", "Inspector", "Nurse", "Dr", "Doctor", "Pharmacist",
    "Dispatcher", "Clerk", "Mrs", "Mr", "Ms", "Sergeant", "Detective",
    "Officer", "Captain", "Professor",
}

_CAPITALIZED_WORD = re.compile(r"\b[A-Z][a-z]+\b")


def load_manifest() -> list[dict[str, Any]]:
    with open(os.path.join(STORIES_DIR, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)["stories"]


def load_story(story_dir: str, variant: str) -> dict[str, Any]:
    path = os.path.join(STORIES_DIR, story_dir, f"{variant}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def thread_aliases(label: str) -> set[str]:
    """Heuristically extract character-name aliases from a thread label.

    Takes the segment before the first comma (the character-identifying
    part of the label, by this dataset's own convention -- see
    data/stories/*/original.json's `threads[].label`) and returns every
    capitalized word in it that isn't a generic title/article.
    """
    first_segment = label.split(",")[0]
    words = _CAPITALIZED_WORD.findall(first_segment)
    return {w for w in words if w not in _TITLE_STOPWORDS}


def _opening_words(text: str, n: int) -> str:
    return " ".join(text.split()[:n])


def name_opening_rate(story: dict[str, Any]) -> dict[str, float]:
    """Per-thread fraction of events whose opening words name that thread's
    character. Threads with no extractable alias (e.g. "the crew") are
    reported with rate 0.0 and are not a leakage concern by this check."""
    aliases_by_thread = {t["id"]: thread_aliases(t["label"]) for t in story["threads"]}
    events_by_thread: dict[str, list[dict]] = {t["id"]: [] for t in story["threads"]}
    for event in story["events"]:
        events_by_thread.setdefault(event["thread_id"], []).append(event)

    rates = {}
    for thread_id, events in events_by_thread.items():
        aliases = aliases_by_thread.get(thread_id, set())
        if not events or not aliases:
            rates[thread_id] = 0.0
            continue
        opens_with_name = sum(
            1 for e in events
            if any(alias in _opening_words(e["text"], OPENING_WINDOW) for alias in aliases)
        )
        rates[thread_id] = opens_with_name / len(events)
    return rates


def trivial_lexical_baseline_accuracy(story: dict[str, Any]) -> float:
    """Predict each event's thread by pure alias string-matching anywhere in
    the text (no semantic reasoning), then score with AWT-F1's own
    thread_attribution_accuracy. A single unified predicted-event set is
    built for the whole story so cross-thread name collisions are visible."""
    aliases_by_thread = {t["id"]: thread_aliases(t["label"]) for t in story["threads"]}

    predicted_events = []
    for event in story["events"]:
        best_thread, best_alias_len = None, -1
        for thread_id, aliases in aliases_by_thread.items():
            for alias in aliases:
                if alias in event["text"] and len(alias) > best_alias_len:
                    best_thread, best_alias_len = thread_id, len(alias)
        predicted_events.append({"id": event["id"], "thread_id": best_thread})

    return thread_attribution_accuracy(story["events"], predicted_events)


def audit_story(story: dict[str, Any]) -> dict[str, Any]:
    rates = name_opening_rate(story)
    baseline_accuracy = trivial_lexical_baseline_accuracy(story)
    over_threshold = {
        thread_id: rate for thread_id, rate in rates.items()
        if rate > NAME_OPENING_RATE_THRESHOLD
    }
    return {
        "name_opening_rate": rates,
        "threads_over_threshold": over_threshold,
        "trivial_baseline_accuracy": baseline_accuracy,
        "baseline_over_threshold": baseline_accuracy > TRIVIAL_BASELINE_ACCURACY_THRESHOLD,
    }


def main() -> None:
    manifest = load_manifest()
    any_failure = False

    for entry in manifest:
        story = load_story(entry["dir"], "original")
        result = audit_story(story)

        print(f"{entry['id']}:")
        for thread_id, rate in sorted(result["name_opening_rate"].items()):
            flag = " <-- OVER THRESHOLD" if thread_id in result["threads_over_threshold"] else ""
            print(f"  thread {thread_id}: name-opening rate = {rate:.2f}{flag}")
        flag = " <-- OVER THRESHOLD" if result["baseline_over_threshold"] else ""
        print(f"  trivial lexical-baseline thread-attribution accuracy = "
              f"{result['trivial_baseline_accuracy']:.3f}{flag}")
        print()

        if result["threads_over_threshold"] or result["baseline_over_threshold"]:
            any_failure = True

    if any_failure:
        print(f"LEAKAGE DETECTED: one or more stories exceed the thresholds "
              f"(name-opening rate > {NAME_OPENING_RATE_THRESHOLD}, "
              f"trivial-baseline accuracy > {TRIVIAL_BASELINE_ACCURACY_THRESHOLD}). "
              f"See docs/hypothesis_expansion_and_leakage_remediation_plan.md.")
        sys.exit(1)
    else:
        print("OK: no story exceeds the thread-attribution leakage thresholds.")


if __name__ == "__main__":
    main()
