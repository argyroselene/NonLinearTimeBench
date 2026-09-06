"""Runs the direct one-shot baseline (pipeline/direct_baseline.py) against a
live LLM for all 5 real stories -- this has never been done before this
script; direct_baseline.py was previously only unit-tested against
FixtureLLMClient. This gives H3 (direct-prompting vs. graph pipeline) its
first real data point.

The direct baseline produces only a global_order (a flat chronological
ordering), not pairwise Allen-interval relations -- it never reasons about
"overlaps"/"during"/"meets", only "comes before/after". To score it with
AWT-F1's relation_score (which expects an allen_relation per gold edge), we
derive the coarsest-possible predicted relation for each gold edge pair from
their relative position in global_order: "before" or "after". This is
maximally generous to the baseline (any node pair the model ordered
consistently with gold's stated precedence scores the same partial credit
edge_score("before", "before") would give -- see metrics/allen_relations.py)
while remaining honest about what the method can express: it structurally
cannot ever score >0 on a gold edge whose true relation isn't before/after
(e.g. "overlaps", "during"), which is a real, reportable limitation of the
baseline, not a metric artifact.

Output: web/src/data/predictions/story_XX_direct.json (kept separate from
the graph pipeline's story_XX.json so the web UI's existing fixtures aren't
touched).

Provider is selectable via LLM_PROVIDER=featherless|groq (default
featherless, requires FEATHERLESS_API_KEY, model override FEATHERLESS_MODEL)
or LLM_PROVIDER=groq (free tier, requires GROQ_API_KEY, model override
GROQ_MODEL) -- see generate_real_predictions.py's docstring for why.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from pipeline.llm_client import FeatherlessLLMClient, GroqLLMClient
from pipeline.direct_baseline import run_direct_baseline
from metrics.awt_f1 import awt_f1
from metrics.allen_relations import edge_score

STORIES_DIR = os.path.join(ROOT, "data", "stories")
OUT_DIR = os.path.join(ROOT, "web", "src", "data", "predictions")

PROVIDER = os.environ.get("LLM_PROVIDER", "featherless")
if PROVIDER == "groq":
    CLIENT_CLASS = GroqLLMClient
    MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
else:
    CLIENT_CLASS = FeatherlessLLMClient
    MODEL = os.environ.get("FEATHERLESS_MODEL", "Qwen/Qwen2.5-72B-Instruct")


def load_story(story_dir, variant):
    path = os.path.join(STORIES_DIR, story_dir, f"{variant}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def passage_from_story(story):
    by_id = {e["id"]: e for e in story["events"]}
    ordered_ids = sorted(by_id, key=lambda i: int(i[1:]))
    return [by_id[i]["text"] for i in ordered_ids]


def normalize_id(node_id):
    """The model is instructed to always prefix ids with "s" (see
    direct_baseline_prompt), but real models sometimes drop it anyway
    (observed on story_01: "10" instead of "s10"). Normalizing here keeps
    scoring robust to that formatting slip without silently masking any
    genuine reasoning error -- ids are otherwise passed through unchanged."""
    node_id = str(node_id)
    return node_id if node_id.startswith("s") else f"s{node_id}"


def normalize_result_ids(result):
    for event in result["events"]:
        event["id"] = normalize_id(event["id"])
    result["global_order"] = [normalize_id(i) for i in result["global_order"]]
    result["convergence_points"] = [
        [normalize_id(i) for i in pair] for pair in result["convergence_points"]
    ]
    return result


def derive_edges_from_order(global_order, gold_edges):
    """For each gold edge's node pair, if both nodes appear in global_order,
    derive a coarse "before"/"after" predicted relation from their relative
    position. Missing nodes are simply omitted (relation_score treats a
    missing predicted edge as 0, same as any other unpredicted gold edge)."""
    position = {node_id: i for i, node_id in enumerate(global_order)}
    derived = []
    for e in gold_edges:
        i, j = e["node_i"], e["node_j"]
        if i not in position or j not in position:
            continue
        relation = "before" if position[i] < position[j] else "after"
        derived.append({"node_i": i, "node_j": j, "allen_relation": relation})
    return derived


def scored_edges(gold_edges, derived_edges):
    """Per-edge score for the web UI's Graph3D rendering (mirrors the
    scored_edges helper in generate_counterfactual_predictions.py /
    rescore_predictions.py). derived_edges only ever asserts "before"/"after"
    (see module docstring), so predicted_relation is None -- and score 0.0 --
    for any gold pair whose two nodes weren't both present in global_order."""
    predicted_map = {(e["node_i"], e["node_j"]): e["allen_relation"] for e in derived_edges}
    predicted_map.update({(e["node_j"], e["node_i"]): e["allen_relation"] for e in derived_edges})
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

    only = os.environ.get("ONLY_STORIES")
    if only:
        wanted = set(only.split(","))
        manifest = [entry for entry in manifest if entry["id"] in wanted]

    for entry in manifest:
        story = load_story(entry["dir"], "original")
        passage = passage_from_story(story)
        print(f"-- {entry['id']} ({len(story['events'])} events) --", flush=True)

        client = CLIENT_CLASS(model=MODEL)
        result = run_direct_baseline(passage, client)
        result = normalize_result_ids(result)
        result["model"] = MODEL

        derived_edges = derive_edges_from_order(result["global_order"], story["edges"])
        scoring_view = {
            "events": result["events"],
            "edges": derived_edges,
            "convergence_points": result["convergence_points"],
        }
        scores = awt_f1(story, scoring_view)
        result["derived_edges"] = derived_edges
        result["scored_edges"] = scored_edges(story["edges"], derived_edges)
        result["awt_f1_scores"] = scores

        out_path = os.path.join(OUT_DIR, f"{entry['dir']}_direct.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"{entry['id']}: awt_f1={scores['awt_f1']:.3f} "
              f"(relation={scores['relation_score']:.3f}, "
              f"thread={scores['thread_attribution_accuracy']:.3f}, "
              f"convergence={scores['convergence_f1']:.3f}) "
              f"-> {out_path}")


if __name__ == "__main__":
    main()
