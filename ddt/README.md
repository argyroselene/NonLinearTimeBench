# NonLinearTimeBench

A research benchmark and pipeline for measuring how well LLMs reconstruct the
true time structure of **nonlinear narratives** — stories told across
multiple interleaved threads, flashbacks, and cross-thread convergence
points — rather than a single chronology presented out of order.

## The question

When a narrative is genuinely nonlinear, how much of a language model's
apparent temporal reasoning ability survives, how much of what does survive
is memorized world-knowledge rather than text-grounded inference, and does
decomposing the task into an explicit, checkable pipeline recover any of
that gap — and reveal exactly *where* reasoning breaks down?

Two methods are compared on the same passages, scored by the same metric:

- **Direct baseline** — one-shot prompt: read the shuffled passage, output
  thread labels, a full chronological order, and any cross-thread
  convergence points.
- **Graph pipeline** — decomposes the task into extraction, deterministic
  repair, and deterministic verification stages (below), so failures can be
  localized to a specific stage instead of being one opaque wrong answer.

## Method

### The graph pipeline

```
passage → node extraction (LLM) → edge extraction (LLM)
        → Path-Consistency Repair (deterministic)
        → per-thread topological sort (deterministic)
        → Convergence-Order Consistency verification (deterministic)
        → cross-thread alignment → final graph
```

1. **Node extraction** — every sentence gets an id and a thread label.
2. **Edge extraction** — pairwise Allen interval-algebra relations between
   sentences, plus candidate cross-thread convergence points (sentences
   describing the same moment from different threads).
3. **Path-Consistency Repair (PCR)** — checks every same-thread triangle of
   predicted edges against Allen's composition table and repairs
   transitivity violations to the relation closest to the model's original
   prediction, only when there's enough independent evidence; otherwise it
   logs the conflict rather than guessing.
4. **Per-thread topological sort** — deterministic ordering via each
   thread's own precedence edges.
5. **Convergence-Order Consistency (COC)** — verifies which candidate
   convergence points are mutually order-consistent with each thread's own
   computed sequence (via longest-increasing-subsequence), filtering out
   candidates that can't actually hold together.
6. **Cross-thread alignment** — merges the per-thread orders into one final
   global timeline at the verified convergence anchors.

### The metric — AWT-F1

Plain Exact Match collapses toward zero on long sequences even when a model
is nearly right; Kendall's tau only ever asks "before or after," discarding
11 of Allen's 13 relations. AWT-F1 is the harmonic mean of three sub-scores,
built so each failure mode stays visible instead of being averaged away:

- **Relation score** — partial credit for near-misses, using a distance
  derived from how many of the 6 pairwise interval-endpoint comparisons two
  Allen relations disagree on (not copied from a diagram — derived directly
  from each relation's formal definition).
- **Thread-attribution accuracy** — the model invents its own thread labels,
  so this is scored against the best label correspondence to gold, not
  string equality.
- **Convergence F1** — precision/recall/F1 over cross-thread same-moment
  pairs.

The harmonic mean returns exactly 0 if any one sub-score is 0 — deliberate,
so a single broken dimension can't hide behind two working ones. Full
formulas and a complete worked example: [`kaggle_backup/awt_f1_field_guide.html`](kaggle_backup/awt_f1_field_guide.html).

Because most stories carry only 1-2 gold convergence points, a per-story
convergence score is a high-variance statistic on its own — `pooled_convergence_f1`
pools convergence pairs across the whole story set instead, which is what
the web demo's sidebar shows.

### Dataset

5 hand-authored pilot stories (`data/stories/`), each with three variants:

- **original** — the shuffled, numbered passage as fed to the model.
- **counterfactual** — entity names substituted, same gold graph shape, for
  testing whether apparent temporal reasoning is text-grounded or memorized.
- **linear** — a presentation-order relabeling of the same gold graph, used
  as a single-chronology control condition.

All 13 Allen relations appear somewhere in the set; each story stresses a
different nonlinearity mechanism — converging threads, flashback framing,
dual-direction narration, overlapping-duration timelines.

## Results so far (pilot scale, honest)

- **Direct prompting beats the graph pipeline on relation accuracy**, on
  every story tested. The pipeline's structured decomposition doesn't
  translate into a higher score by itself.
- **Thread attribution is essentially solved** (~0.9-1.0 across the set).
- **Convergence-point detection is the dominant, near-total failure mode.**
  This is the actual bottleneck driving low AWT-F1 scores — not relation
  extraction, not thread attribution.
- **A dedicated "recall critique" pipeline stage (CRC)** — a second LLM call
  asking specifically what cross-thread convergence pairs the first pass
  missed — was designed, implemented, and tested with a methodologically
  sound matched-pair ablation (both conditions forked from one shared
  extraction call, to rule out the run-to-run non-determinism that a naive
  two-independent-runs comparison can't control for). Result: **it does not
  help, and regressed one story's score.** This is a real negative result,
  not a bug — see `PLAN_AND_STATUS.md` §5.3a for the full record, including
  a self-correction of an earlier, over-read positive finding.
- Four independent mitigation attempts on convergence detection (three
  prompt-format redesigns plus CRC) have now failed the same way, which is
  evidence the bottleneck is closer to a base-model interval-endpoint
  reasoning limitation than a prompting or pipeline-architecture problem.
  The next diagnostic step — not yet run — is testing whether a
  frontier-class model shows the same failure.

The pipeline's demonstrated value right now is **diagnostic**: it's the
reason any of the above is known at all, rather than one opaque global
score with no way to tell why it's wrong. `PLAN_AND_STATUS.md` is the full,
continuously-updated source of truth for research framing, method
decisions, every experiment actually run, and an honest list of what's
still missing.

## Project structure

```
pipeline/     the 6-stage graph pipeline + direct baseline + LLM client
metrics/      Allen relations, AWT-F1, pooled convergence, significance testing
data/         the pilot dataset (original/counterfactual/linear per story)
scripts/      dataset authoring/validation, prediction generation, analysis
tests/        pytest suite for metrics and pipeline stages
web/          interactive 3D viewer (React + Vite + three.js)
docs/         related work, metric writeup, hypothesis-expansion plan
kaggle_backup/  local-model fallback (notebook + packaged pipeline code)
```

## Setup

### Pipeline & metrics (Python)

```bash
pip install -r requirements.txt
cp .env.local.example .env.local   # add your GROQ_API_KEY and/or FEATHERLESS_API_KEY
python -m pytest tests/ -q
```

Generate predictions against a live model:

```bash
python scripts/generate_real_predictions.py          # graph pipeline, original variant
python scripts/generate_direct_baseline_predictions.py
python scripts/generate_counterfactual_predictions.py
LLM_PROVIDER=groq python scripts/generate_crc_matched_predictions.py  # CRC ablation
```

No live API available? `kaggle_backup/nonlineartime_kaggle_backup.ipynb`
reruns the same pipeline code against a local open-weight model on a free
Kaggle GPU.

### Web demo

```bash
cd web
npm install
npm run dev
```

## Key design decisions

- **Node correspondence is handled by construction** (shared sentence-number
  IDs between gold and predicted graphs), not by a Hungarian/optimal-
  assignment matcher — a deliberate scope limitation for this synthetic,
  sentence-anchored pilot dataset, not a general solution.
- **PCR/COC are deterministic and zero-LLM-cost** — they only ever verify or
  repair candidates a model already proposed; they can't invent recall a
  model never generated. That's precisely the gap CRC was built to test.
- **Every prompt/schema change and every experiment result is logged in
  `PLAN_AND_STATUS.md`**, including corrections to earlier readings of the
  data, on the principle that a research-integrity-relevant mistake belongs
  in the permanent record, not just in conversation.
