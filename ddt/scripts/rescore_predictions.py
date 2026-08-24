"""Recomputes awt_f1_scores/awt_f1_scores_unrepaired for already-generated
prediction JSON files against current gold data, without re-calling any LLM.

Use after a metrics/awt_f1.py change (e.g. the thread_attribution_accuracy
label-invariance fix), or after a change to a deterministic pipeline stage
(e.g. convergence_verification.py), to refresh web/src/data/predictions/
story_XX.json in place, cheaply, instead of burning further LLM quota on a
change that doesn't touch what the model itself produced.

Also recomputes thread_orders/convergence_points/global_order from each
prediction's already-saved events/edges/raw_convergence_points, since those
are pure functions of that data (stages 3-4 of the pipeline, deterministic,
no LLM involved).
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from metrics.awt_f1 import awt_f1
from pipeline.convergence_verification import verify_convergence_points
from pipeline.graph_pipeline import align_convergence_points, topological_sort_per_thread

STORIES_DIR = os.path.join(ROOT, "data", "stories")
PRED_DIR = os.path.join(ROOT, "web", "src", "data", "predictions")


def load_story(story_dir, variant):
    path = os.path.join(STORIES_DIR, story_dir, f"{variant}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def scored_edges(gold_edges, predicted_edges):
    from metrics.allen_relations import edge_score

    predicted_map = {(e["node_i"], e["node_j"]): e["allen_relation"] for e in predicted_edges}
    predicted_map.update({(e["node_j"], e["node_i"]): e["allen_relation"] for e in predicted_edges})
    scored = []
    for e in gold_edges:
        key = (e["node_i"], e["node_j"])
        predicted_relation = predicted_map.get(key)
        score = edge_score(e["allen_relation"], predicted_relation) if predicted_relation else 0.0
        scored.append({
            "node_i": e["node_i"],
            "node_j": e["node_j"],
            "gold_relation": e["allen_relation"],
            "predicted_relation": predicted_relation,
            "score": score,
        })
    return scored


def main():
    with open(os.path.join(STORIES_DIR, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)["stories"]

    for entry in manifest:
        pred_path = os.path.join(PRED_DIR, f"{entry['dir']}.json")
        if not os.path.exists(pred_path):
            print(f"-- {entry['id']}: no prediction file, skipping --")
            continue

        with open(pred_path, encoding="utf-8") as f:
            result = json.load(f)
        if "raw_edges" not in result:
            print(f"-- {entry['id']}: fixture-based prediction (no raw_edges), skipping --")
            continue

        story = load_story(entry["dir"], "original")

        raw_convergence_points = result.get("raw_convergence_points", result.get("candidate_convergence_pairs", []))
        result["raw_convergence_points"] = raw_convergence_points

        thread_orders = topological_sort_per_thread(result["events"], result["edges"])
        convergence_points, convergence_verification_log = verify_convergence_points(
            result["events"], thread_orders, raw_convergence_points
        )
        result["thread_orders"] = thread_orders
        result["convergence_points"] = convergence_points
        result["convergence_verification_log"] = convergence_verification_log
        result["global_order"] = align_convergence_points(thread_orders, convergence_points)

        old_awt_f1 = result.get("awt_f1_scores", {}).get("awt_f1")
        scores = awt_f1(story, result)
        result["scored_edges"] = scored_edges(story["edges"], result["edges"])
        result["awt_f1_scores"] = scores

        unrepaired = dict(result, edges=result["raw_edges"], convergence_points=raw_convergence_points)
        scores_unrepaired = awt_f1(story, unrepaired)
        result["scored_edges_unrepaired"] = scored_edges(story["edges"], result["raw_edges"])
        result["awt_f1_scores_unrepaired"] = scores_unrepaired

        with open(pred_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        delta = scores["awt_f1"] - scores_unrepaired["awt_f1"]
        print(f"{entry['id']}: awt_f1={scores['awt_f1']:.3f} "
              f"(was {old_awt_f1:.3f}) "
              f"(relation={scores['relation_score']:.3f}, "
              f"thread={scores['thread_attribution_accuracy']:.3f}, "
              f"convergence={scores['convergence_f1']:.3f}) "
              f"| unrepaired={scores_unrepaired['awt_f1']:.3f} "
              f"| repair_delta={delta:+.3f}")


if __name__ == "__main__":
    main()
