"""Applies the thread-attribution leakage remediation to the AUTHORING SOURCES.

The original remediation (scripts/_apply_leakage_fix.py) edited the generated
data/stories/story_XX/*.json files directly. Those files are regenerated from
data/authoring/story_XX.json by scripts/split_stories.py, so the very next
regeneration silently reverted every fix -- which is exactly what happened.
Editing the source makes the fix durable.

Both text tracks get the same replacement, because every replacement sentence
is deliberately pronoun/role-based with no character name in it; there is
nothing for the counterfactual track to perturb in those specific sentences.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
AUTHORING_DIR = os.path.join(ROOT, "data", "authoring")

from scripts._apply_leakage_fix import (
    STORY_01_EDITS,
    STORY_02_EDITS,
    STORY_03_EDITS,
    STORY_04_EDITS,
    STORY_05_EDITS,
)

EDITS = {
    "story_01": STORY_01_EDITS,
    "story_02": STORY_02_EDITS,
    "story_03": STORY_03_EDITS,
    "story_04": STORY_04_EDITS,
    "story_05": STORY_05_EDITS,
}


def main():
    for story_id, edits in EDITS.items():
        path = os.path.join(AUTHORING_DIR, f"{story_id}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        applied = 0
        for event in data["events"]:
            if event["id"] in edits:
                event["text"] = edits[event["id"]]
                if "cf_text" in event:
                    event["cf_text"] = edits[event["id"]]
                applied += 1

        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"{story_id}: applied {applied}/{len(edits)} edits to the authoring source")


if __name__ == "__main__":
    main()
