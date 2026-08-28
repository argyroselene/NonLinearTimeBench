"""Coverage-check script for the pilot dataset (plan §3 / §6 build step 2).

Verifies, across data/stories/story_*/{original,counterfactual}.json:
  - every one of the 13 Allen relations appears at least once somewhere in the set
  - each story has 3-6 threads, each thread has 9-12 events
  - each story has 3-7 cross-thread edges (edges whose two nodes are in different
    threads -- the scale-up's density target, a superset of convergence_points)
  - each original/counterfactual pair shares the same graph shape (same node ids,
    same edge relation labels between the same node pairs, same convergence points)
    -- this is what the Caliper-style perturbation promises: renamed surface text,
    identical gold structure. This is now a regression guard, not the primary
    correctness guarantee -- that moved upstream to scripts/split_stories.py,
    which makes the two variants identical by construction.
  - each story's `linear` variant (the H1 control condition) is an id-relabeling of
    `original`'s graph, via the `id_map_from_original` scripts/split_stories.py
    already records -- i.e. applying that map to `original`'s edges/events/
    convergence_points must reproduce `linear`'s exactly. This is the regression
    guard for the "linear is a presentation-order variant of the same gold graph,
    never a different graph" guarantee.
"""

import json
import os
import sys
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from metrics.allen_relations import RELATIONS

STORIES_DIR = os.path.join(ROOT, "data", "stories")


def load_manifest() -> list[dict[str, Any]]:
    with open(os.path.join(STORIES_DIR, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)["stories"]


def load_story(story_dir: str, variant: str) -> dict[str, Any]:
    path = os.path.join(STORIES_DIR, story_dir, f"{variant}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def structural_signature(story: dict[str, Any]) -> tuple[list, list, list]:
    edge_sig = sorted(
        (e["node_i"], e["node_j"], e["allen_relation"]) for e in story["edges"]
    )
    thread_sig = sorted(e["id"] for e in story["events"])
    conv_sig = sorted(tuple(sorted(pair)) for pair in story["convergence_points"])
    return edge_sig, thread_sig, conv_sig


def events_per_thread(story: dict[str, Any]) -> dict[str, int]:
    counts = {t["id"]: 0 for t in story["threads"]}
    for e in story["events"]:
        counts[e["thread_id"]] += 1
    return counts


def cross_thread_edge_count(story: dict[str, Any]) -> int:
    thread_of = {e["id"]: e["thread_id"] for e in story["events"]}
    return sum(
        1 for edge in story["edges"]
        if thread_of[edge["node_i"]] != thread_of[edge["node_j"]]
    )


def linear_matches_original(original: dict[str, Any], linear: dict[str, Any]) -> bool:
    """True if `linear` is exactly `original`'s graph relabeled via
    `linear["id_map_from_original"]` -- never a structurally different graph."""
    id_map = linear.get("id_map_from_original")
    if not id_map or set(id_map) != {e["id"] for e in original["events"]}:
        return False

    remapped_edges = sorted(
        (id_map[e["node_i"]], id_map[e["node_j"]], e["allen_relation"]) for e in original["edges"]
    )
    linear_edges = sorted((e["node_i"], e["node_j"], e["allen_relation"]) for e in linear["edges"])
    if remapped_edges != linear_edges:
        return False

    remapped_conv = sorted(tuple(sorted((id_map[a], id_map[b]))) for a, b in original["convergence_points"])
    linear_conv = sorted(tuple(sorted(pair)) for pair in linear["convergence_points"])
    if remapped_conv != linear_conv:
        return False

    if set(id_map.values()) != {e["id"] for e in linear["events"]}:
        return False

    return True


def main() -> None:
    manifest = load_manifest()
    relation_coverage = {r: 0 for r in RELATIONS}
    errors = []

    for entry in manifest:
        original = load_story(entry["dir"], "original")
        counterfactual = load_story(entry["dir"], "counterfactual")
        linear = load_story(entry["dir"], "linear")

        n_events = len(original["events"])
        n_threads = len(original["threads"])
        if not (3 <= n_threads <= 6):
            errors.append(f"{entry['id']}: {n_threads} threads (need 3-6)")

        per_thread = events_per_thread(original)
        for thread_id, count in per_thread.items():
            if not (9 <= count <= 12):
                errors.append(f"{entry['id']}: thread {thread_id} has {count} events (need 9-12)")

        n_cross = cross_thread_edge_count(original)
        if not (3 <= n_cross <= 7):
            errors.append(f"{entry['id']}: {n_cross} cross-thread edges (need 3-7)")

        for edge in original["edges"]:
            relation_coverage[edge["allen_relation"]] += 1

        orig_sig = structural_signature(original)
        cf_sig = structural_signature(counterfactual)
        if orig_sig != cf_sig:
            errors.append(f"{entry['id']}: original/counterfactual graphs differ structurally")

        if not linear_matches_original(original, linear):
            errors.append(f"{entry['id']}: linear variant is not a valid id-relabeling of original")

        print(f"{entry['id']}: {n_events} events, {n_threads} threads, "
              f"{len(original['edges'])} edges, {n_cross} cross-thread, "
              f"{len(original['convergence_points'])} convergence point(s)")

    print()
    print("Allen relation coverage across the pilot set:")
    missing = []
    for r in RELATIONS:
        count = relation_coverage[r]
        print(f"  {r:15s} {count}")
        if count == 0:
            missing.append(r)

    if missing:
        errors.append(f"missing Allen relations entirely: {missing}")

    print()
    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"OK: all 13 Allen relations covered, all {len(manifest)} stories meet the "
              f"3-6 thread / 9-12 event-per-thread / 3-7 cross-thread-edge targets, "
              f"all counterfactual twins are structurally identical to their originals, "
              f"all linear variants are valid id-relabelings of their originals.")


if __name__ == "__main__":
    main()
