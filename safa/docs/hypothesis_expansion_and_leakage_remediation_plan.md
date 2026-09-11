# Hypothesis Expansion & Thread-Attribution Leakage Remediation Plan

**Status: proposed, not yet actioned.** This document is a plan for user
review before any code or dataset changes are made. Once approved, execute
it and record completion in `PLAN_AND_STATUS.md` (§1 for new hypotheses, §6
for the remediation milestone), moving superseded text to its Changelog per
that document's own convention — do not duplicate status tracking here.

Written 2026-09-05, in direct response to two user requests: (1) suggest
additional hypotheses beyond H1-H3a, and (2) build a concrete plan to fix
the thread-attribution leakage identified this session (see below).

---

## Part 1 — Proposed new hypotheses

All four are chosen because they reuse data or infrastructure that already
exists (or is already scoped in §6), so none requires new dataset authoring
beyond what's already planned for the N=20 scale-up. Numbered continuing
from the existing H1/H2/H3/H3a.

### H4 — Repair-stage value-add (PCR/COC ablation)

> The deterministic repair/verification stages (PCR, COC) measurably improve
> AWT-F1 and its sub-scores over the graph pipeline's raw, unrepaired LLM
> output — i.e., the repair mechanism itself is doing real work, not just
> the graph decomposition.

**Why this is worth adding**: right now the pipeline's contribution is
argued only indirectly (H3 compares the *whole* graph pipeline to direct
prompting, and lost). H4 isolates the piece this project actually built
(PCR/COC) from the piece it didn't invent (the LLM's raw extraction),
which is a cleaner and more specific claim for a thesis to defend even if
H3 stays negative.

**Cost to test**: near-zero. `scripts/rescore_predictions.py` and the
existing prediction JSONs already carry both `awt_f1_scores` (post-repair)
and `awt_f1_scores_unrepaired` (§6 statistical protocol already lists this
exact comparison as planned for `metrics/significance.py`, just not yet
framed as its own hypothesis). This can be computed today for all 5 pilot
stories with no new API calls.

### H5 — Convergence-detection bottleneck is a base-model capability ceiling, not a task-design flaw

> A stronger/differently-trained model (the planned Groq secondary model,
> `openai/gpt-oss-120b`) shows materially better raw convergence-candidate
> recall than Qwen2.5-72B-Instruct on the same stories, indicating the
> bottleneck identified in §5.3 is a base-model interval-endpoint-reasoning
> limitation rather than a fundamental property of the task.

**Why this is worth adding**: §5.5 already names this as "the single
highest-value next experiment if any additional model budget becomes
available" — you already have that budget (Groq, free tier) and it's
already scoped for M5. Stating it as a named hypothesis rather than a
side-check gives it a clear pass/fail criterion for the thesis (recall
improves by more than run-to-run noise vs. it doesn't) and turns the
existing convergence-bottleneck finding into a two-model comparison instead
of a single-model dead end.

**Cost to test**: the Groq wiring already exists (`GroqLLMClient`); this
only requires running the already-planned second-model pass and comparing
raw convergence-candidate recall (pre-COC) between models, not just the
final AWT-F1.

### H6 — Failure severity scales with narrative complexity

> AWT-F1 (and specifically convergence-F1) degrades as a function of
> narrative complexity — number of threads, number of gold convergence
> points, or total event count — across the N=20 story set, rather than
> failing uniformly regardless of complexity.

**Why this is worth adding**: it's a natural regression/correlation
analysis over metadata every story already carries (`manifest.json`'s
thread/event counts, gold `convergence_points` length), and it strengthens
the "convergence detection is the bottleneck" finding by showing *where*
along a complexity axis it breaks down, rather than treating all 5-20
stories as an undifferentiated pool. It also gives the thesis a chart that
isn't just a bar comparison — a genuine trend line — which is useful for
the defense.

**Cost to test**: zero new data. A small analysis script over the N=20
results once M8 (`scripts/statistical_analysis.py`) exists.

### H7 — With leakage removed, thread attribution becomes a genuine reasoning signal

> Once the thread-attribution leakage fix (Part 2, below) is applied,
> thread-attribution accuracy is no longer saturated at ~1.0 and instead
> shows measurable degradation under multi-thread and counterfactual
> conditions — recovering the reasoning-cost signal H1 originally
> predicted for this sub-dimension, which the pilot data could not detect
> because the sub-metric was saturated by design (see Part 2).

**Why this is worth adding**: this is the direct, honest follow-through on
the leakage finding from this session. Right now H1's evidence can only
come from relation/convergence sub-scores, because thread attribution is
provably uninformative in the current 5 pilot stories (§Part 2 below). H7
gives you a clean, falsifiable claim to report either way: if accuracy
*still* stays near 1.0 after the leakage fix, that's itself informative
(thread attribution really is easy for this model family, independent of
naming); if it drops, that confirms the leak was masking a real difficulty
signal.

**Cost to test**: requires the Part 2 remediation to be done first, then
re-running predictions on the affected stories — already necessary work,
not additional work.

**Not recommended for this scope**: a fine-tuning/model-scaling hypothesis
(RQ6-style) or a human-baseline hypothesis — both already correctly ruled
out in §4.3 as infrastructure the team doesn't have. Adding them now would
recreate the over-scoping problem the M1.1 pivot was meant to fix.

---

## Part 2 — Thread-attribution leakage remediation plan

### 2.1 The problem, stated precisely

Inspecting `data/stories/story_01/original.json` directly (not from memory):
every event sentence opens by naming its thread's one character, and each
character maps 1:1 to exactly one thread for the entire story (e.g. Farrow ↔
thread A, Tanner ↔ thread L, Dawson ↔ thread S). Thread-attribution accuracy
is 1.000 across all 5 pilot stories, in every condition tested, including
under the counterfactual (entity-renamed) condition, with one exception
(story_04 collapses to 0.044 under counterfactual — see 2.6, this is a
separate, useful signal, not the leak). A sub-score that is saturated at
ceiling regardless of condition is not measuring what H1/H3a claim it
measures — it's closer to a keyword lookup than a reasoning test.

### 2.2 Diagnostic tooling to build first (before touching any story text)

A leakage fix without a measurement is just a guess. Build a small,
deterministic, no-LLM-call script — `scripts/check_thread_leakage.py` — with
two checks, run over every story's `original.json`:

1. **Name-opening rate**: for each thread, the fraction of that thread's
   events whose text's first N tokens (N=3, configurable) contain the
   character's canonical name or a registered alias. Report per-thread and
   per-story.
2. **Trivial lexical-baseline classifier**: a zero-LLM, keyword-only
   classifier that predicts `thread_id` for each event purely from whether
   the character's name/alias string appears anywhere in the text (no
   semantic reasoning at all — a `str.contains` lookup). Score this
   classifier's thread-attribution accuracy the same way AWT-F1's
   thread-attribution sub-score is computed. **This is the number that
   actually settles the question**: if a dumb string-match baseline already
   scores ~1.0, the sub-metric cannot possibly be testing reasoning,
   regardless of what the LLM's score is.

**Acceptance thresholds (proposed, open for user sign-off)**:
- Name-opening rate: **≤ 40%** of a thread's events may open with the
  character's literal name.
- Trivial lexical-baseline accuracy: **≤ 0.85** thread-attribution accuracy
  story-wide (leaves headroom below the ceiling for a real model's genuine
  performance to be distinguishable from the trivial floor).

This script is small (well under the 800-line ceiling), belongs alongside
`scripts/check_coverage.py` (same authoring-integrity-tooling category), and
should get a unit test (`tests/test_check_thread_leakage.py`) per this
project's own testing conventions for `scripts/` — technically optional
under this project's relaxed `scripts/` coverage rule, but cheap enough here
(pure string logic) that skipping it isn't worth the risk of a silent bug in
the one script whose entire job is catching a subtle bug.

### 2.3 Authoring guidelines (for both remediated old stories and the 15 new ones)

To be added to the hybrid-authoring outline template referenced in §6 of
`PLAN_AND_STATUS.md` (the human-outline step that precedes the LLM draft
step), as explicit constraints the outline-writer and the drafting LLM must
both follow:

1. **Vary reference form.** After a character's first mention within a
   contiguous run of that thread's sentences, prefer pronouns ("he," "she")
   or role/definite descriptions ("the pilot," "the boy on the sand," "the
   boatman") over repeating the proper name. Only reintroduce the proper
   name when narrative clarity genuinely requires it (e.g., after a long
   gap from other threads' sentences).
2. **Allow cross-thread name mentions that are not attribution signals.**
   Occasionally let one thread's event mention another thread's character
   by name in passing (dialogue, a radio call, a rumor) without that event
   belonging to that character's thread. This directly tests whether the
   model is attributing by *whose event this is* rather than *which name
   appears in the text*.
3. **Avoid one-name-per-thread-for-the-whole-story as an absolute rule.**
   Where the narrative allows it, let two characters in the same thread (or
   a character referred to differently across scenes — rank, nickname,
   relationship term) appear, so thread identity has to be tracked via
   narrative continuity/context, not a fixed string.
4. **Keep gold-graph structure completely unaffected.** These are
   surface-text changes only — `events[].thread_id`, `edges`,
   `convergence_points` stay exactly as authored; only how the *text*
   refers to characters changes. This keeps the fix orthogonal to the
   PCR/COC pipeline mechanics validated so far.

### 2.4 Scope decision: rewrite the 5 existing pilot stories, or only apply this to the 15 new ones?

**Recommendation: rewrite the text of all 5 existing pilot stories** (gold
graph structure unchanged), rather than leaving them as a leaky subset of
the final N=20 set. Reasoning:

- The N=20 scale-up already requires re-running every generation script
  (original, counterfactual, linear, direct, both models) per §6 — the pilot
  numbers currently in §5.2 were always going to be superseded by the N=20
  run, not kept as final results. Fixing the 5 pilot stories' text now adds
  no new re-run pass beyond what M5/M6/M8 already schedule.
- A final dataset where 5/20 stories have a known, documented leak and 15/20
  don't is a much harder methodology section to write and defend than "we
  found and fixed a leak before scaling up" — the current asymmetry would
  need to be caveated in every downstream table.
- Cost is small: 5 stories' worth of text edits (structure-preserving,
  `check_coverage.py`'s existing structural-signature diff can verify
  `original`/`counterfactual` twins stay in sync after the rewrite) plus
  5 stories' worth of re-run API calls, which is a fraction of the N=20
  scale-up's total budget.

**Open question for user sign-off**: confirm this recommendation before
work starts, since it does mean discarding the current pilot numbers in
§5.2 as "final" (they were already going to be superseded by N=20, but this
makes that explicit and immediate rather than incidental).

### 2.5 Execution steps, in order

1. Build `scripts/check_thread_leakage.py` (+ unit test). Run it against the
   current 5 stories to get a concrete, numeric baseline of how bad the leak
   currently is (not just the qualitative observation from this session).
2. Get explicit user sign-off on: the acceptance thresholds in 2.2, and the
   rewrite-all-5 decision in 2.4.
3. Rewrite the 5 pilot stories' `original.json`/`counterfactual.json` text
   per the guidelines in 2.3, preserving gold graph structure exactly.
   Re-run `scripts/check_coverage.py` to confirm structural twins still
   match, then re-run `scripts/check_thread_leakage.py` until both stories
   clear the thresholds.
4. Bake the same guidelines (2.3) into the hybrid-authoring outline template
   used for the 15 new stories, and run `check_thread_leakage.py` on each
   new story as part of its authoring checklist — before it's considered
   "done," not as a late audit.
5. Re-run all real-model prediction scripts for the 5 remediated pilot
   stories (`generate_real_predictions.py`, `generate_direct_baseline_
   predictions.py`, `generate_counterfactual_predictions.py`) to get
   post-remediation numbers. Update `PLAN_AND_STATUS.md` §5.2 in place,
   moving the current pre-remediation pilot table to the Changelog rather
   than deleting it (per that document's own convention) — the old numbers
   remain a documented, honest artifact of "what the leaky version showed,"
   which is itself worth keeping for the thesis's methodology chapter as an
   example of catching and fixing a validity threat.
6. Register H4-H7 (Part 1) in `PLAN_AND_STATUS.md` §1.1 alongside H1-H3a,
   and update §4.1's experiment-tracking table with rows for each.

### 2.6 One thing this remediation should NOT obscure

`story_04`'s thread-attribution collapse under the counterfactual condition
(1.000 → 0.044, §5.2) already happened *despite* the leaky name-per-sentence
design — meaning something about the counterfactual's entity substitution
specifically broke the trivial name-lookup shortcut for that one story
(worth checking why: did the substituted names in story_04 collide across
threads, or become ambiguous in some way the other 4 stories' substitutions
didn't?). That's a real, separate, pre-existing finding and should be
investigated and reported on its own terms, not folded into or lost inside
this remediation effort.

### 2.7 Placement in the team timeline

This entire remediation (tooling + rewriting 5 stories + guideline update)
fits inside the **Weeks 1-2** window already allocated in `thesis_plan.html`
to "methodology freeze + web functional pass," immediately before Stream B
starts outlining the 15 new stories — this is exactly the right moment to
do it, since it changes the authoring guidelines those 15 stories will
follow. Doing it later (after some or all of the 15 are drafted) would mean
re-authoring already-completed stories, which is precisely the rework
PLAN_AND_STATUS.md's N=20 scoping note was trying to avoid.

---

## Summary of what needs a decision before work starts

1. Approve or adjust the two acceptance thresholds in §2.2 (40% name-opening
   rate, 0.85 trivial-baseline accuracy).
2. Approve rewriting the text of all 5 existing pilot stories (§2.4), or
   choose an alternative (e.g., leave them as a documented exception).
3. Approve adding H4-H7 as stated, or adjust/drop any of them.

Nothing in this document has been executed yet — no code written, no story
text changed, no `PLAN_AND_STATUS.md` edits made. This is the plan only.
