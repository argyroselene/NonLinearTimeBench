"""One-off helper (not part of the permanent scripts/ toolkit) that shortens
story_05 by dropping its "P" thread (Clerk Odom, shift-report filing).

Rationale: story_05 was too slow to run through the live pipeline (54 events,
6 threads -- the largest pilot story) and repeatedly stalled on retries. The
P thread has zero cross-thread edges and isn't referenced by any convergence
point, so dropping it removes 9 events/8 edges cleanly without touching the
story's cross-thread structure (stays at 7, the dataset's max) or any Allen
relation that appears only once dataset-wide (checked against
scripts/check_coverage.py's per-relation counts before running this).

Result: 5 threads / 45 events / 46 edges / 7 cross-thread links, still within
check_coverage.py's 3-6 thread / 9-12 event-per-thread / 3-7 cross-thread
targets.
"""

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORY_DIR = os.path.join(ROOT, "data", "stories", "story_05")

DROP_THREAD = "P"
NEW_SOURCE_NOTE = "5 threads / 45 events / 7 cross-thread links"


def load(variant):
    with open(os.path.join(STORY_DIR, f"{variant}.json"), encoding="utf-8") as f:
        return json.load(f)


def save(variant, data):
    with open(os.path.join(STORY_DIR, f"{variant}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def trim_variant(data, dropped_event_ids):
    data["threads"] = [t for t in data["threads"] if t["id"] != DROP_THREAD]
    data["events"] = [e for e in data["events"] if e["id"] not in dropped_event_ids]
    data["edges"] = [
        e for e in data["edges"]
        if e["node_i"] not in dropped_event_ids and e["node_j"] not in dropped_event_ids
    ]
    data["convergence_points"] = [
        pair for pair in data["convergence_points"]
        if pair[0] not in dropped_event_ids and pair[1] not in dropped_event_ids
    ]
    if "5 threads / 45 events" not in data.get("source", ""):
        data["source"] = data["source"].replace(
            "expanded to 6 threads / 54 events / 7 cross-thread links",
            f"expanded, then trimmed to {NEW_SOURCE_NOTE} (P thread dropped for pipeline runtime)",
        )
    return data


def main():
    original = load("original")
    counterfactual = load("counterfactual")
    linear = load("linear")

    dropped_orig_ids = {e["id"] for e in original["events"] if e["thread_id"] == DROP_THREAD}
    dropped_linear_ids = {
        linear_id for orig_id, linear_id in linear["id_map_from_original"].items()
        if orig_id in dropped_orig_ids
    }

    original = trim_variant(original, dropped_orig_ids)
    counterfactual = trim_variant(counterfactual, dropped_orig_ids)
    linear = trim_variant(linear, dropped_linear_ids)
    linear["id_map_from_original"] = {
        orig_id: linear_id for orig_id, linear_id in linear["id_map_from_original"].items()
        if orig_id not in dropped_orig_ids
    }

    save("original", original)
    save("counterfactual", counterfactual)
    save("linear", linear)

    print(f"story_05: dropped thread {DROP_THREAD} ({len(dropped_orig_ids)} events) from "
          f"original/counterfactual/linear -> {len(original['events'])} events, "
          f"{len(original['threads'])} threads, {len(original['edges'])} edges remain")


if __name__ == "__main__":
    main()
