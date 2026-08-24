"""Runs the TRUE CRC ablation: pipeline.graph_pipeline.run_graph_pipeline_matched,
which shares one node/edge-extraction call between both the no-CRC and CRC
results instead of running two independent pipelines. This is the fix for
the confound documented in PLAN_AND_STATUS.md §5.3a, where two separate
extraction calls for the same story returned different convergence
candidates at temperature 0, with no CRC involvement -- making the earlier
paired-but-independent comparison (scripts/generate_crc_predictions.py)
unable to isolate CRC's actual effect.

Provider is selectable via LLM_PROVIDER=featherless|groq (see
generate_real_predictions.py's docstring for why both exist). Output:
web/src/data/predictions/story_XX_matched_baseline.json and
story_XX_matched_crc.json -- kept separate from every other prediction file
so this is purely additive.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from pipeline.llm_client import FeatherlessLLMClient, GroqLLMClient
from pipeline.graph_pipeline import run_graph_pipeline_matched
from metrics.awt_f1 import awt_f1, scored_edges

STORIES_DIR = os.path.join(ROOT, "data", "stories")
OUT_DIR = os.path.join(ROOT, "web", "src", "data", "predictions")

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



def score_and_save(story, result, out_path):
    result["model"] = MODEL
    scores = awt_f1(story, result)
    result["scored_edges"] = scored_edges(story["edges"], result["edges"], result.get("global_order"))
    result["awt_f1_scores"] = scores
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return scores


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
        print(f"-- {entry['id']} matched ablation ({len(story['events'])} events) --", flush=True)

        client = CLIENT_CLASS(model=MODEL)
        without_crc, with_crc = run_graph_pipeline_matched(passage, client)

        base_path = os.path.join(OUT_DIR, f"{entry['dir']}_matched_baseline.json")
        crc_path = os.path.join(OUT_DIR, f"{entry['dir']}_matched_crc.json")
        scores_without = score_and_save(story, without_crc, base_path)
        scores_with = score_and_save(story, with_crc, crc_path)

        delta = scores_with["convergence_f1"] - scores_without["convergence_f1"]
        print(f"{entry['id']}: no-CRC convergence={scores_without['convergence_f1']:.3f} "
              f"| CRC convergence={scores_with['convergence_f1']:.3f} "
              f"(delta {delta:+.3f}) | recall_critique_added={len(with_crc['recall_critique_added'])}")


if __name__ == "__main__":
    main()
