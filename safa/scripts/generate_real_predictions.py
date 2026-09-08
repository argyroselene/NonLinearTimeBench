"""Generates REAL graph-pipeline predictions using a live LLM (Groq free-tier
open model), replacing generate_predictions.py's FixtureLLMClient mock.

generate_predictions.py never calls a model: it builds "predictions" straight
from each story's own gold node/edge data, then applies a hand-picked
DEGRADATIONS override -- useful for demoing the PCR repair mechanism in
isolation, but the resulting AWT-F1 gap vs. gold is synthetic, not a measure
of actual model behavior. This script runs the real node/edge extraction
stages against a live model instead, so predicted-vs-gold AWT-F1 reflects
genuine extraction errors.

Provider is selectable via LLM_PROVIDER=featherless|groq (default featherless,
requires FEATHERLESS_API_KEY, model override FEATHERLESS_MODEL) or
LLM_PROVIDER=groq (free tier, requires GROQ_API_KEY, model override
GROQ_MODEL). Added because Featherless is a paid subscription that can lapse
(see PLAN_AND_STATUS.md Changelog, 2026-09-09) while Groq's free tier has no
billing risk -- useful as a fallback, at the cost of mixing models across the
pilot set if only some stories are (re)run with it.

Output: web/src/data/predictions/story_XX.json, overwriting the fixture-based
files with real-model results (same schema, so the web UI needs no changes).
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from pipeline.llm_client import FeatherlessLLMClient, GroqLLMClient
from pipeline.graph_pipeline import run_graph_pipeline
from metrics.awt_f1 import awt_f1, scored_edges

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



def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(STORIES_DIR, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)["stories"]

    only = os.environ.get("ONLY_STORIES")
    if only:
        wanted = set(only.split(","))
        manifest = [entry for entry in manifest if entry["id"] in wanted]

    for entry in manifest:
        print(f"-- {entry['id']} ({len(load_story(entry['dir'], 'original')['events'])} events) --", flush=True)
        story = load_story(entry["dir"], "original")
        passage = passage_from_story(story)

        client = CLIENT_CLASS(model=MODEL)
        result = run_graph_pipeline(passage, client)
        result["model"] = MODEL

        scores = awt_f1(story, result)
        result["scored_edges"] = scored_edges(story["edges"], result["edges"], result.get("global_order"))
        result["awt_f1_scores"] = scores

        unrepaired = dict(result, edges=result["raw_edges"], convergence_points=result["raw_convergence_points"])
        scores_unrepaired = awt_f1(story, unrepaired)
        result["scored_edges_unrepaired"] = scored_edges(story["edges"], result["raw_edges"], result.get("global_order"))
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
