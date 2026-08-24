"""Builds a story's gold graph from an interval spec, instead of hand-asserting it.

The original five stories had their Allen relations typed in by hand alongside
the prose, so nothing stopped a label from disagreeing with the timeline the
text actually describes. Here the author supplies each event's real interval
(start, end on a shared integer timeline) and which pairs a reader could
actually infer a relation between; every gold label is then DERIVED via
metrics.allen_relations.relation_from_intervals. A gold graph built this way
is correct by construction, and the relation distribution is a design
parameter the author can tune rather than an accident of what got typed.

A spec is a Python dict (see data/authoring/*.spec.py) with:

    threads: [{"id", "label", "granularity"}]
    events:  [{"id", "thread_id", "start", "end", "time_expr", "text"}]
    edges:   [[node_i, node_j], ...]      # relation is computed, not given
    convergence_points: [[node_i, node_j], ...]   # validated as simultaneous

Usage:
    python scripts/build_story.py data/authoring/story_06.spec.py --report
    python scripts/build_story.py data/authoring/story_06.spec.py --write
"""

import argparse
import collections
import itertools
import json
import os
import runpy
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from metrics.allen_relations import RELATIONS, relation_from_intervals

STORIES_DIR = os.path.join(ROOT, "data", "stories")


def load_spec(path):
    return runpy.run_path(path)["SPEC"]


def build_gold(spec):
    """Derive the gold edge set (with computed relations) from the intervals."""
    by_id = {e["id"]: e for e in spec["events"]}
    edges = []
    for node_i, node_j in spec["edges"]:
        a, b = by_id[node_i], by_id[node_j]
        relation = relation_from_intervals(a["start"], a["end"], b["start"], b["end"])
        edges.append({
            "node_i": node_i,
            "node_j": node_j,
            "allen_relation": relation,
            "evidence_span": f"{a['time_expr']} vs {b['time_expr']}",
        })
    return edges


def convergence_pool(spec):
    """Every cross-thread pair that genuinely shares a boundary instant.

    This is the judged set for closure-aware convergence precision (see
    metrics.awt_f1.convergence_scores). `convergence_points` stays the small,
    narratively salient subset used for recall; without this pool, a model that
    correctly identifies a real simultaneity nobody annotated is scored as a
    false positive -- which is what drove convergence to 0.000 across the board.

    Pairs where both events merely span the story frame (both starting at the
    global start, or both ending at the global end) are excluded: two
    twelve-hour shifts both beginning at 22:00 share an instant trivially, and
    counting that as a detectable "shared moment" rewards noise. This mirrors
    TempEval-3's reduction step, which strips trivially derivable edges before
    scoring.
    """
    events = spec["events"]
    frame_start = min(e["start"] for e in events)
    frame_end = max(e["end"] for e in events)

    pool = []
    for a, b in itertools.combinations(events, 2):
        if a["thread_id"] == b["thread_id"]:
            continue
        shared = {a["start"], a["end"]} & {b["start"], b["end"]}
        if not shared:
            continue
        instant = sorted(shared)[0]
        both_frame_start = a["start"] == b["start"] == frame_start
        both_frame_end = a["end"] == b["end"] == frame_end
        if both_frame_start or both_frame_end:
            continue
        pool.append([a["id"], b["id"]])
    return pool


def validate(spec, edges):
    """Structural and semantic checks. Returns a list of problems."""
    problems = []
    by_id = {e["id"]: e for e in spec["events"]}
    thread_ids = {t["id"] for t in spec["threads"]}

    if not (3 <= len(spec["threads"]) <= 6):
        problems.append(f"{len(spec['threads'])} threads (need 3-6)")

    per_thread = collections.Counter(e["thread_id"] for e in spec["events"])
    for thread_id in thread_ids:
        count = per_thread.get(thread_id, 0)
        if not (9 <= count <= 12):
            problems.append(f"thread {thread_id} has {count} events (need 9-12)")
    for thread_id in per_thread:
        if thread_id not in thread_ids:
            problems.append(f"event assigned to undeclared thread {thread_id!r}")

    for event in spec["events"]:
        if event["start"] > event["end"]:
            problems.append(f"{event['id']}: end precedes start")

    cross = sum(
        1 for e in edges
        if by_id[e["node_i"]]["thread_id"] != by_id[e["node_j"]]["thread_id"]
    )
    if not (3 <= cross <= 7):
        problems.append(f"{cross} cross-thread edges (need 3-7)")

    # convergence points must genuinely be the same instant, across threads
    for node_i, node_j in spec["convergence_points"]:
        a, b = by_id[node_i], by_id[node_j]
        if a["thread_id"] == b["thread_id"]:
            problems.append(f"convergence {node_i}/{node_j}: same thread")
        shared = {a["start"], a["end"]} & {b["start"], b["end"]}
        if not shared:
            problems.append(
                f"convergence {node_i}/{node_j}: intervals share no instant "
                f"({a['start']}-{a['end']} vs {b['start']}-{b['end']})"
            )

    # a thread-attribution shortcut check: no event text may open with a name
    # drawn from its own thread label (the leakage failure this dataset already
    # had to be remediated for once)
    for thread in spec["threads"]:
        names = {w for w in thread["label"].split(",")[0].split() if w[:1].isupper()}
        for event in spec["events"]:
            if event["thread_id"] != thread["id"]:
                continue
            opening = " ".join(event["text"].split()[:4])
            for name in names:
                if name in opening:
                    problems.append(
                        f"{event['id']}: opens with its own thread's name {name!r} "
                        f"-- recoverable by string match, not reasoning"
                    )
    return problems


def report(spec, edges):
    dist = collections.Counter(e["allen_relation"] for e in edges)
    total = sum(dist.values())
    order_only = sum(dist[r] for r in ("before", "after"))

    print(f"{spec['story_id']}: {len(spec['events'])} events, "
          f"{len(spec['threads'])} threads, {total} edges, "
          f"{len(spec['convergence_points'])} convergence points")
    print("\nrelation distribution:")
    for relation in RELATIONS:
        count = dist.get(relation, 0)
        bar = "#" * count
        print(f"  {relation:15} {count:3}  {count/total:5.1%} {bar}")
    print(f"\nbefore/after share: {order_only/total:.1%} "
          f"(lower = harder for an order-only method to fake)")
    missing = [r for r in RELATIONS if not dist.get(r)]
    if missing:
        print(f"relations absent from this story: {', '.join(missing)}")


def to_authoring_json(spec, edges):
    """Emit the data/authoring/story_XX.json that split_stories.py consumes to
    produce the original/counterfactual/linear variants.

    The counterfactual text track is generated by substituting the entity
    names in spec["counterfactual_names"] rather than being written out by
    hand, so the two tracks cannot drift apart in anything except the
    substituted surface forms -- which is exactly the invariant the
    memorization control depends on.
    """
    renames = spec.get("counterfactual_names", {})

    def perturb(text):
        for original, replacement in renames.items():
            text = text.replace(original, replacement)
        return text

    events = []
    for event in spec["events"]:
        events.append({
            "id": event["id"],
            "thread_id": event["thread_id"],
            "time_expr": event["time_expr"],
            # The perturbation is entity identity, not the clock: the
            # counterfactual must keep the SAME temporal structure so the gold
            # graph stays valid for both tracks. Shifting the stated times here
            # would also contradict the prose, which states times in words.
            "cf_time_expr": event["time_expr"],
            "text": event["text"],
            "cf_text": perturb(event["text"]),
        })

    threads = []
    for thread in spec["threads"]:
        threads.append({
            "id": thread["id"],
            "label": thread["label"],
            "cf_label": perturb(thread["label"]),
            "granularity": thread["granularity"],
        })

    return {
        "story_id": spec["story_id"],
        "cf_story_id": f"{spec['story_id']}_cf",
        "title": spec["title"],
        "cf_title": perturb(spec["title"]),
        "source": spec.get("source", ""),
        "cf_source": f"Perturbed twin of {spec['story_id']} -- same gold graph, renamed entities",
        "threads": threads,
        "events": events,
        "edges": edges,
        "convergence_points": [list(p) for p in spec["convergence_points"]],
        "convergence_pool": convergence_pool(spec),
    }


def to_story_json(spec, edges, variant):
    events = []
    for event in spec["events"]:
        events.append({
            "id": event["id"],
            "thread_id": event["thread_id"],
            "time_expr": event["time_expr"],
            "text": event["text"],
        })
    return {
        "story_id": f"{spec['story_id']}{'' if variant == 'original' else '_' + variant}",
        "title": spec["title"],
        "source": spec.get("source", "Hand-authored; gold relations derived from event intervals"),
        "threads": spec["threads"],
        "events": events,
        "edges": edges,
        "convergence_points": [list(p) for p in spec["convergence_points"]],
        "convergence_pool": convergence_pool(spec),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    edges = build_gold(spec)
    problems = validate(spec, edges)

    if args.report:
        report(spec, edges)
        print()

    if problems:
        print("VALIDATION FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)
    print("validation OK")

    if args.write:
        authoring_dir = os.path.join(ROOT, "data", "authoring")
        os.makedirs(authoring_dir, exist_ok=True)
        path = os.path.join(authoring_dir, f"{spec['story_id']}.json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(to_authoring_json(spec, edges), f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"wrote {path}")
        print("now run: python scripts/split_stories.py   (builds all three variants)")


if __name__ == "__main__":
    main()
