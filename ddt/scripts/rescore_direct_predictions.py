"""Adds scored_edges to already-generated story_XX_direct.json files without
re-calling the LLM. derived_edges/global_order are already saved and are pure
functions of the model's original output, so this only recomputes the
deterministic per-edge scoring view (see scored_edges() in
generate_direct_baseline_predictions.py) needed for the web UI's Graph3D
rendering, mirroring rescore_predictions.py's approach for the graph pipeline.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))

from generate_direct_baseline_predictions import scored_edges

STORIES_DIR = os.path.join(ROOT, "data", "stories")
PRED_DIR = os.path.join(ROOT, "web", "src", "data", "predictions")


def main():
    with open(os.path.join(STORIES_DIR, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)["stories"]

    for entry in manifest:
        pred_path = os.path.join(PRED_DIR, f"{entry['dir']}_direct.json")
        if not os.path.exists(pred_path):
            print(f"-- {entry['id']}: no direct-baseline prediction file, skipping --")
            continue

        with open(os.path.join(STORIES_DIR, entry["dir"], "original.json"), encoding="utf-8") as f:
            story = json.load(f)
        with open(pred_path, encoding="utf-8") as f:
            result = json.load(f)

        result["scored_edges"] = scored_edges(story["edges"], result["derived_edges"])

        with open(pred_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"{entry['id']}: added scored_edges ({len(result['scored_edges'])} gold edges) -> {pred_path}")


if __name__ == "__main__":
    main()
