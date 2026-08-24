"""Splits each data/authoring/story_XX.json (single source of graph structure +
two parallel text tracks) into data/stories/story_XX/{original,counterfactual,linear}.json.

original/counterfactual are guaranteed structurally identical by construction: this
script copies `threads[].id`/`granularity`, `events[].id`/`thread_id`, `edges[]`,
and `convergence_points[]` verbatim into both outputs, and only ever picks between
the `text`/`cf_text` (etc.) fields depending on the variant being emitted. There is
no code path that can attach different threads/events/edges to the two variants.

`linear` (the H1 control condition -- see PLAN_AND_STATUS.md/M6) is a third variant
of the SAME gold graph as `original`, not a new story: it presents the identical
events in the model's own gold chronological order (computed via
pipeline.graph_pipeline's topological_sort_per_thread + align_convergence_points,
the same deterministic stages 3-4 the pipeline runs on predictions) instead of the
authored shuffled/interleaved order. Because ids double as sentence-number-in-the-
passage (pipeline/prompts.py's node-correspondence convention), reordering the
passage means every event must be relabeled to a new sequential id matching its new
position -- `_build_linear_variant` does this relabeling and rewrites edges/
convergence_points through the same id map, so the linear variant's graph is an
isomorphic relabeling of `original`'s, never a different graph.
"""

import json
import os
import sys
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
AUTHORING_DIR = os.path.join(ROOT, "data", "authoring")
STORIES_DIR = os.path.join(ROOT, "data", "stories")

from pipeline.graph_pipeline import align_convergence_points, topological_sort_per_thread


def _build_linear_variant(original: dict[str, Any]) -> dict[str, Any]:
    """Relabels `original`'s events/edges/convergence_points into gold
    chronological order, so ids are sequential in presentation order again."""
    nodes = [{"id": e["id"], "thread_id": e["thread_id"]} for e in original["events"]]
    thread_orders = topological_sort_per_thread(nodes, original["edges"])
    global_order = align_convergence_points(thread_orders, original["convergence_points"])

    original_ids = {e["id"] for e in original["events"]}
    assert len(global_order) == len(original_ids) and set(global_order) == original_ids, (
        "topological_sort_per_thread/align_convergence_points must return an exact "
        "permutation of original's event ids"
    )

    id_map = {old_id: f"s{i + 1}" for i, old_id in enumerate(global_order)}
    events_by_id = {e["id"]: e for e in original["events"]}

    events = [
        {
            "id": id_map[old_id],
            "thread_id": events_by_id[old_id]["thread_id"],
            "time_expr": events_by_id[old_id]["time_expr"],
            "text": events_by_id[old_id]["text"],
        }
        for old_id in global_order
    ]
    edges = [
        {
            "node_i": id_map[e["node_i"]],
            "node_j": id_map[e["node_j"]],
            "allen_relation": e["allen_relation"],
            "evidence_span": e["evidence_span"],
        }
        for e in original["edges"]
    ]
    convergence_points = [[id_map[a], id_map[b]] for a, b in original["convergence_points"]]

    return {
        "story_id": original["story_id"] + "_linear",
        "title": original["title"] + " (linear order)",
        "source": original["source"],
        "threads": [dict(t) for t in original["threads"]],
        "events": events,
        "edges": edges,
        "convergence_points": convergence_points,
        "id_map_from_original": id_map,
    }


def split_one(authoring: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    def make_variant(is_cf: bool) -> dict[str, Any]:
        threads = [
            {
                "id": t["id"],
                "label": t["cf_label"] if is_cf else t["label"],
                "granularity": t["granularity"],
            }
            for t in authoring["threads"]
        ]
        events = [
            {
                "id": e["id"],
                "thread_id": e["thread_id"],
                "time_expr": e["cf_time_expr"] if is_cf else e["time_expr"],
                "text": e["cf_text"] if is_cf else e["text"],
            }
            for e in authoring["events"]
        ]
        edges = [
            {
                "node_i": e["node_i"],
                "node_j": e["node_j"],
                "allen_relation": e["allen_relation"],
                "evidence_span": (e.get("cf_evidence_span") or e["evidence_span"]) if is_cf else e["evidence_span"],
            }
            for e in authoring["edges"]
        ]
        convergence_points = [list(pair) for pair in authoring["convergence_points"]]

        variant = {
            "story_id": authoring["cf_story_id"] if is_cf else authoring["story_id"],
            "title": authoring["cf_title"] if is_cf else authoring["title"],
            "source": authoring["cf_source"] if is_cf else authoring["source"],
            "threads": threads,
            "events": events,
            "edges": edges,
            "convergence_points": convergence_points,
        }
        # The judged pool of formally valid simultaneities, when the story was
        # built from an interval spec. Structural (id-level), so it is
        # identical across both text tracks. See
        # metrics.awt_f1.convergence_scores for why precision needs it.
        if "convergence_pool" in authoring:
            variant["convergence_pool"] = [list(pair) for pair in authoring["convergence_pool"]]
        return variant

    return make_variant(False), make_variant(True)


def main() -> None:
    story_dirs = sorted(
        d for d in os.listdir(AUTHORING_DIR) if d.startswith("story_") and d.endswith(".json")
    )
    if not story_dirs:
        print(f"No authoring files found in {AUTHORING_DIR}", file=sys.stderr)
        sys.exit(1)

    for fname in story_dirs:
        story_key = fname[: -len(".json")]  # e.g. "story_01"
        with open(os.path.join(AUTHORING_DIR, fname), encoding="utf-8") as f:
            authoring = json.load(f)

        original, counterfactual = split_one(authoring)
        linear = _build_linear_variant(original)

        out_dir = os.path.join(STORIES_DIR, story_key)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "original.json"), "w", encoding="utf-8") as f:
            json.dump(original, f, indent=2)
        with open(os.path.join(out_dir, "counterfactual.json"), "w", encoding="utf-8") as f:
            json.dump(counterfactual, f, indent=2)
        with open(os.path.join(out_dir, "linear.json"), "w", encoding="utf-8") as f:
            json.dump(linear, f, indent=2)

        print(f"{story_key}: {len(original['events'])} events, {len(original['threads'])} threads, "
              f"{len(original['edges'])} edges -> {out_dir}")


if __name__ == "__main__":
    main()
