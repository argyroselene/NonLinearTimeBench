"""Runs the graph pipeline WITH the Convergence Recall Critique (CRC) stage
enabled (pipeline/graph_pipeline.py's use_recall_critique=True) and scores it
against the same gold graphs used by generate_real_predictions.py.

CRC is a research addition, not a silent change to the default pipeline: the
existing scripts/generate_real_predictions.py still calls run_graph_pipeline
with use_recall_critique defaulting to False, so its already-reported numbers
are untouched. This script exists specifically to produce the paired
with/without-CRC comparison for the web demo and, eventually, the N=20
ablation (PLAN_AND_STATUS.md's convergence-recall gap).

Set USE_CRC=0 to run the SAME model with the stage disabled instead --
needed because the existing story_XX.json baseline was generated on a
different model (Qwen2.5-72B/Featherless) than this script's current default
(Groq), so comparing CRC-on against that stale baseline would confound "did
CRC help" with "did the model change." USE_CRC=0 produces a same-model,
no-CRC baseline (story_XX_groq_baseline.json) to diff against instead.

Provider is selectable via LLM_PROVIDER=featherless|groq (see
generate_real_predictions.py's docstring for why both exist). Output:
web/src/data/predictions/story_XX_crc.json, or story_XX_groq_baseline.json
when USE_CRC=0 (kept separate from story_XX.json so the baseline-vs-CRC
comparison in the web UI can show both without touching reported numbers).
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

USE_CRC = os.environ.get("USE_CRC", "1") != "0"
OUT_SUFFIX = "_crc" if USE_CRC else "_groq_baseline"

PROVIDER = os.environ.get("LLM_PROVIDER", "groq")
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
        story = load_story(entry["dir"], "original")
        passage = passage_from_story(story)
        label = "with CRC" if USE_CRC else "same-model no-CRC baseline"
        print(f"-- {entry['id']} {label} ({len(story['events'])} events) --", flush=True)

        client = CLIENT_CLASS(model=MODEL)
        result = run_graph_pipeline(passage, client, use_recall_critique=USE_CRC)
        result["model"] = MODEL

        scores = awt_f1(story, result)
        result["scored_edges"] = scored_edges(story["edges"], result["edges"], result.get("global_order"))
        result["awt_f1_scores"] = scores

        out_path = os.path.join(OUT_DIR, f"{entry['dir']}{OUT_SUFFIX}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"{entry['id']}: awt_f1={scores['awt_f1']:.3f} "
              f"(relation={scores['relation_score']:.3f}, "
              f"thread={scores['thread_attribution_accuracy']:.3f}, "
              f"convergence={scores['convergence_f1']:.3f}) "
              f"| recall_critique_added={len(result['recall_critique_added'])} "
              f"-> {out_path}")


if __name__ == "__main__":
    main()
