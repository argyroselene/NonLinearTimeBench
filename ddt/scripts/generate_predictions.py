"""Generates mock graph-pipeline predictions for the web UI's comparison mode
(plan build-order step 5).

Runs the real graph pipeline (deterministic stages 3-4 included) against each
story's passage, using FixtureLLMClient scripted from that story's own gold
node/edge data -- optionally degraded on a couple of stories -- so comparison
mode has genuine per-edge AWT-F1 scores to color, not hand-faked numbers.

Output: web/src/data/predictions/story_XX.json, each holding the pipeline's
full result plus a `scored_edges` list (every gold edge annotated with the
predicted relation found and its Allen edge_score) for the UI to render
directly without recomputing metrics client-side.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from pipeline.llm_client import FixtureLLMClient
from pipeline.graph_pipeline import run_graph_pipeline
from metrics.allen_relations import edge_score
from metrics.awt_f1 import awt_f1

STORIES_DIR = os.path.join(ROOT, "data", "stories")
OUT_DIR = os.path.join(ROOT, "web", "src", "data", "predictions")

# Deliberate imperfections so comparison mode has something to show, keyed by
# story id -> {"relation_overrides": {(node_i, node_j): wrong_relation},
#              "drop_convergence": bool, "drop_edge": (node_i, node_j) or None}
DEGRADATIONS = {
    "story_01": {
        "relation_overrides": {("s2", "s5"): "meets"},
        "drop_convergence": False,
        "drop_edge": None,
    },
    "story_02": {
        "relation_overrides": {},
        "drop_convergence": True,
        "drop_edge": None,
    },
    "story_03": {
        "relation_overrides": {("s3", "s2"): "before"},
        "drop_convergence": False,
        "drop_edge": None,
    },
    "story_04": {
        # s1-s5 is witnessed by 2 independent triangles that both force
        # "overlaps" -- a real target for PCR to confidently repair.
        "relation_overrides": {("s3", "s1"): "before", ("s1", "s5"): "before"},
        "drop_convergence": False,
        "drop_edge": None,
    },
    "story_05": {
        "relation_overrides": {("s2", "s1"): "before"},
        "drop_convergence": False,
        "drop_edge": None,
    },
}


def load_story(story_dir, variant):
    path = os.path.join(STORIES_DIR, story_dir, f"{variant}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def passage_from_story(story):
    by_id = {e["id"]: e for e in story["events"]}
    ordered_ids = sorted(by_id, key=lambda i: int(i[1:]))
    return [by_id[i]["text"] for i in ordered_ids]


def build_fixture_responses(story, degradation):
    nodes = [{"id": e["id"], "thread_id": e["thread_id"]} for e in story["events"]]

    edges = []
    for e in story["edges"]:
        relation = e["allen_relation"]
        override = degradation["relation_overrides"].get((e["node_i"], e["node_j"]))
        if override:
            relation = override
        if degradation["drop_edge"] == (e["node_i"], e["node_j"]):
            continue
        edges.append({"node_i": e["node_i"], "node_j": e["node_j"], "allen_relation": relation})

    convergence_pairs = [] if degradation["drop_convergence"] else list(story["convergence_points"])

    node_response = {"events": nodes}
    edge_response = {"edges": edges, "candidate_convergence_pairs": convergence_pairs}
    return node_response, edge_response


def scored_edges(gold_edges, predicted_edges):
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
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(STORIES_DIR, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)["stories"]

    for entry in manifest:
        story = load_story(entry["dir"], "original")
        passage = passage_from_story(story)
        degradation = DEGRADATIONS.get(
            entry["id"], {"relation_overrides": {}, "drop_convergence": False, "drop_edge": None}
        )

        node_response, edge_response = build_fixture_responses(story, degradation)
        client = FixtureLLMClient([node_response, edge_response])
        result = run_graph_pipeline(passage, client)

        scores = awt_f1(story, result)
        result["scored_edges"] = scored_edges(story["edges"], result["edges"])
        result["awt_f1_scores"] = scores

        unrepaired = dict(result, edges=result["raw_edges"])
        scores_unrepaired = awt_f1(story, unrepaired)
        result["scored_edges_unrepaired"] = scored_edges(story["edges"], result["raw_edges"])
        result["awt_f1_scores_unrepaired"] = scores_unrepaired

        out_path = os.path.join(OUT_DIR, f"{entry['dir']}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        delta = scores["awt_f1"] - scores_unrepaired["awt_f1"]
        print(f"{entry['id']}: awt_f1={scores['awt_f1']:.3f} "
              f"(relation={scores['relation_score']:.3f}, "
              f"thread={scores['thread_attribution_accuracy']:.3f}, "
              f"convergence={scores['convergence_f1']:.3f}) "
              f"| unrepaired={scores_unrepaired['awt_f1']:.3f} "
              f"| repair_delta={delta:+.3f} "
              f"| repairs={sum(1 for e in result['repair_log'] if e['to_relation'])} "
              f"conflicts={sum(1 for e in result['repair_log'] if e['to_relation'] is None)} "
              f"-> {out_path}")


if __name__ == "__main__":
    main()
