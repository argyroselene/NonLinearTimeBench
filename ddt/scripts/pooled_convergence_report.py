"""Reports dataset-level (pooled) convergence F1 alongside the existing
per-story numbers, for whichever saved prediction set is pointed at.

Per-story convergence_f1 is a high-variance statistic at this dataset's
scale (most stories have only 1-2 gold convergence points), which is why the
harmonic-mean AWT-F1 headline lands on exactly 0.000 so often -- see
metrics/awt_f1.py's pooled_convergence_f1 docstring. This script exists to
show the more stable, dataset-wide alternative using real, already-generated
prediction data (no invented numbers): pass PREDICTION_SUFFIX to pick which
saved prediction set to pool (default "" = the official story_XX.json
real-pipeline predictions).
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from metrics.awt_f1 import convergence_f1, pooled_convergence_f1

STORIES_DIR = os.path.join(ROOT, "data", "stories")
PREDICTIONS_DIR = os.path.join(ROOT, "web", "src", "data", "predictions")


def main():
    suffix = os.environ.get("PREDICTION_SUFFIX", "")
    only = os.environ.get("ONLY_STORIES")

    with open(os.path.join(STORIES_DIR, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)["stories"]
    if only:
        wanted = set(only.split(","))
        manifest = [e for e in manifest if e["id"] in wanted]

    story_results = []
    per_story_f1 = {}
    skipped = []
    for entry in manifest:
        gold_path = os.path.join(STORIES_DIR, entry["dir"], "original.json")
        pred_path = os.path.join(PREDICTIONS_DIR, f"{entry['dir']}{suffix}.json")
        if not os.path.exists(pred_path):
            skipped.append(entry["id"])
            continue
        with open(gold_path, encoding="utf-8") as f:
            gold = json.load(f)
        with open(pred_path, encoding="utf-8") as f:
            predicted = json.load(f)

        gold_points = gold.get("convergence_points", [])
        predicted_points = predicted.get("convergence_points", [])
        story_results.append((entry["id"], gold_points, predicted_points))

        _, _, f1 = convergence_f1(gold_points, predicted_points)
        per_story_f1[entry["id"]] = f1

    print(f"Prediction set: story_XX{suffix or ''}.json\n")
    print("Per-story convergence_f1 (the noisy, 1-2-samples-per-story statistic):")
    for story_id, f1 in per_story_f1.items():
        print(f"  {story_id}: {f1:.3f}")
    if skipped:
        print(f"  (skipped, no prediction file: {', '.join(skipped)})")

    pooled = pooled_convergence_f1(story_results)
    print(f"\nPooled (dataset-level) convergence: "
          f"precision={pooled['precision']:.3f} recall={pooled['recall']:.3f} "
          f"f1={pooled['f1']:.3f} (n_gold_pairs={pooled['n_gold_pairs']}, "
          f"n_predicted_pairs={pooled['n_predicted_pairs']})")


if __name__ == "__main__":
    main()
