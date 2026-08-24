"""Re-scores every saved prediction file in place with the current metric.

No model calls -- every prediction file already stores the raw model output
(events, edges, global_order, convergence points), so correcting a scoring
bug only requires recomputing from what's on disk.

Written after three scoring bugs were found and fixed (see PLAN_AND_STATUS.md):
relation_score ignored the graph pipeline's own global_order while the direct
baseline was scored entirely on order-derived relations; reversed-orientation
edges were compared without inverting the relation; and raw candidate groups
passed to convergence_f1 collapsed to a silent 0.0.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from metrics.awt_f1 import awt_f1, scored_edges

STORIES_DIR = os.path.join(ROOT, "data", "stories")
PREDICTIONS_DIR = os.path.join(ROOT, "web", "src", "data", "predictions")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gold_for(filename):
    """Map a prediction filename back to the gold variant it was scored against."""
    story_dir = filename.split("_")[0] + "_" + filename.split("_")[1].split(".")[0]
    variant = "counterfactual" if "_counterfactual" in filename else "original"
    return load_json(os.path.join(STORIES_DIR, story_dir, f"{variant}.json"))


def main():
    changed = []
    for filename in sorted(os.listdir(PREDICTIONS_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(PREDICTIONS_DIR, filename)
        prediction = load_json(path)
        if "awt_f1_scores" not in prediction:
            continue

        gold = gold_for(filename)
        before = prediction["awt_f1_scores"]

        # The direct baseline stores its order-derived relations in
        # derived_edges; the graph pipeline stores extracted ones in edges.
        edges = prediction.get("edges") or prediction.get("derived_edges") or []
        after = awt_f1(gold, dict(prediction, edges=edges))

        prediction["awt_f1_scores"] = after
        prediction["scored_edges"] = scored_edges(
            gold["edges"], edges, prediction.get("global_order")
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(prediction, f, indent=2)

        changed.append((filename, before, after))

    print(f"{'file':44} {'relation':>18} {'AWT-F1':>18}")
    print("-" * 82)
    for filename, before, after in changed:
        rel = f"{before['relation_score']:.3f} -> {after['relation_score']:.3f}"
        awt = f"{before['awt_f1']:.3f} -> {after['awt_f1']:.3f}"
        print(f"{filename:44} {rel:>18} {awt:>18}")


if __name__ == "__main__":
    main()
