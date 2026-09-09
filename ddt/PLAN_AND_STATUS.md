# PLAN_AND_STATUS.md — NonlinearTime

**This is the single source of truth for this project.** Every future session
should start by reading this file. It is meant to be **updated in place**, not
replaced — when status changes, edit the relevant section and move the
superseded text into the **Changelog** at the bottom rather than deleting it.

**Status as of 2026-09-04: M0-M4 complete, M1 decided, scope pivoted to a
3-person undergraduate thesis (M1.1).** M2/M3/M4 gave H2 and H3 their first
real experimental data (§5.2). **M1.1 decision (2026-09-04, verbatim from the
user): this project is now an undergraduate thesis, done by a 3-person team,
with a ~4-month timeline to defense (from 2026-09-04) — not a solo A*-tier
conference push.** The prior M1 decision's ARR-cycle deadline framing (single
person, October 12, 2026 submission target) is superseded by this pivot and
moved to the Changelog rather than deleted. Dataset scale stays at **N=20**
(the scale already scoped in §6) — not re-scoped yet, to avoid re-authoring
stories if the pipeline methodology changes. **Target is the thesis document
itself; an external paper submission is not a current goal** (may be
revisited later if results are strong, but does not shape scheduling). See
§1.3 for the updated venue framing and §6 for the rescheduled ~16-week
team timeline.

**Update (2026-09-12)**: thread-attribution leakage remediated across all 5
stories (see Changelog); a candidate new pipeline stage, CRC (Convergence
Recall Critique, §5.3a), was designed and tested but its effect is not yet
statistically distinguishable from run-to-run noise at current scale — see
§5.3a for the full honest record, including a self-correction of an
initial over-read of a 2-story result. The AWT-F1 metric's reporting was
also revised: a new pooled (dataset-level) convergence F1 (§3.3 addendum)
replaces per-story convergence scoring as the number worth trusting at
pilot scale, since most stories have only 1-2 gold convergence points.
§5.2's results table predates both changes and is flagged stale in place.

---

## 1. Research framing

### 1.1 Core research question

> When narratives are genuinely nonlinear (multiple interleaved threads,
> flashbacks, and cross-thread convergence points) rather than a single
> chronology presented out of order, how much of an LLM's apparent temporal
> reasoning ability survives, how much of what does survive is memorized
> world-knowledge rather than text-grounded reasoning, and does decomposing
> the task into an explicit, deterministically-checkable graph pipeline
> (extract → repair → verify → sort) recover some of that gap and — critically
> — reveal *where* in the pipeline reasoning actually breaks down?

This decomposes into the three research questions and four hypotheses fixed
in `thesis_blueprint_v2.pdf` (the original planning document for this
project, read in full this session) and echoed in `perplexity.md` (an
external research/strategy pass over the same blueprint):

- **RQ1 / H1**: multi-thread and flashback narratives degrade LLM temporal
  accuracy substantially more than single-chronology shuffling alone
  (isolating thread attribution as an *added* reasoning step, not just more
  events to order).
- **RQ2 / H2**: some portion of apparent temporal ability on real narratives
  is memorized world-knowledge, not text-grounded reasoning — measured as a
  score gap between an "original" passage and a structurally-identical
  "counterfactual" twin (entity names replaced, dates shifted, gold
  permutation unchanged).
- **RQ3 / H3**: a graph-mediated pipeline (extract nodes/threads → extract
  edges → deterministic per-thread topological sort → cross-thread alignment)
  degrades more gracefully than one-shot direct prompting on nonlinear and
  counterfactual conditions, because it turns one opaque global-ordering guess
  into several smaller, individually-checkable steps.
- **H3a (diagnostic)**: the graph pipeline's remaining failures will localize
  to specific stages (originally hypothesized: thread attribution and
  cross-thread alignment) rather than being spread evenly across the pipeline
  — this is the "diagnostic" payoff of decomposing the task at all.

**Important finding that already partially falsifies H3a as originally
stated** (see §5 for the numbers): in the 5-story pilot run so far, thread
attribution accuracy is ~1.0 across every story — it is not a bottleneck at
all. The dominant, near-total failure mode instead is **convergence-point
detection** (cross-thread "same moment" identification), which the harmonic-
mean AWT-F1 metric (see `docs/metric.md`) zeroes out entirely whenever it
fails. This is a genuine, reportable empirical result, not a project
weakness — but it means H3a's specific stage prediction was wrong and the
paper's diagnostic story should be reframed around convergence detection
rather than thread attribution. This reframing is themost novel empirical
content produced so far (see §3 and §5).

### 1.2 Why this is potentially novel

Per the novelty-gap analysis already compiled in `docs/related_work.md` (a
prior research pass in this session, **not independently re-verified in this
pass** — flagged explicitly, see §1.4): no single existing benchmark combines
(a) genuinely multi-thread narrative structure, (b) full Allen's-13-relation
coverage as the edge annotation schema, (c) paired original/counterfactual
memorization control, and (d) a diagnostic stage-wise graph pipeline that
localizes *where* errors occur, not just *whether* they occur. The closest
individual precedents, as cited in `related_work.md` / `paper_draft.md`:

- **Direct predecessor**: the single-chronology shuffled-biography benchmark
  (OpenReview `jogKc4OluB`) this thesis explicitly extends along two axes
  (genuine multi-thread nonlinearity; memorization control).
- **Memorization control precedent**: ContraTable (arXiv 2606.23667),
  CounterBench (arXiv 2502.11008), Caliper (arXiv 2606.04915), "Reasoning or
  Reciting?" (arXiv 2307.02477) — counterfactual perturbation as a method,
  applied to tables/causal-reasoning/general QA, not narrative temporal
  ordering.
- **Graph-repair precedent for this session's new contribution (PCR/COC)**:
  TLEX (arXiv 2406.05265) applies Allen's path-consistency algorithm to
  LLM-extracted TimeML graphs for *detection* of inconsistency only — its own
  paper states automatic correction is future work. To the best of the
  literature review already done (again, not re-verified this pass), no prior
  work uses Allen's composition table as an automatic *repair* mechanism, or
  uses each thread's own already-computed order as a *verification* signal
  for cross-thread convergence candidates.
- **Event-graph similarity metric precedents**: CALLMSAE (arXiv 2406.18449),
  the Set-Aligning Framework (arXiv 2404.01532), GEST (arXiv 2305.12940) — all
  address the same node-correspondence problem AWT-F1 sidesteps by using
  shared sentence-number node IDs (a scope limitation, see §3.4/§5.4), but
  none is Allen-complete or has thread/convergence sub-scores.

### 1.3 Target venue(s)

**Updated 2026-09-04 (M1.1): this project's target is an undergraduate
thesis, produced by a 3-person team over a ~4-month window (from
2026-09-04), with external paper submission explicitly not a current goal.**
The prior ARR/A*-conference framing below (from the 2026-09-03 M1 decision)
is superseded by this pivot and kept only for historical context — see the
Changelog for the full rationale and verbatim decision.

- The blueprint's own dataset target is ~3–4k passages across linear,
  multi-thread, and flashback conditions, with 40–60% counterfactual pairing,
  multiple model families/sizes, and a human baseline. What exists today is
  **5 hand-authored stories**, one model (Qwen2.5-72B-Instruct), with a
  second model (Groq secondary) and counterfactual/linear variants scoped for
  the N=20 scale-up (§6). The thesis target (N=20, one primary model plus one
  secondary-model robustness check, no human baseline) is explicitly smaller
  than the blueprint's original ~3-4k/multi-model/human-baseline scope — this
  is a deliberate, stated scope reduction appropriate to a 3-person
  undergraduate thesis, not a silent shortfall.
- **Superseded framing (2026-09-03 M1 decision, kept for history — see
  Changelog)**: A*-tier venues (ACL/EMNLP/NAACL main, ICLR) expect the scale,
  statistical power, and baseline breadth described in §2.3 of
  `perplexity.md`; at that time the plan was a solo attempt to hit the next
  ARR submission cycle (October 12, 2026). That framing, its deadline
  pressure, and any associated scope-cutting (e.g. "cut Groq if tight," §6's
  prior note) no longer apply now that the project is a 3-person, ~4-month
  thesis with no external-submission goal.
- **Current realistic target**: the **thesis document itself** is the primary
  and only deliverable being scheduled against in this document. A future
  paper submission (workshop or full venue) may be revisited later if the
  N=20 results are strong enough to warrant it, but is explicitly out of
  scope for the ~16-week timeline in §6 and should not shape any near-term
  scheduling decision.

### 1.4 What a positive result would demonstrate, and what would falsify it

- **H1 positive**: nonlinear conditions show a statistically distinguishable
  larger accuracy drop than linear shuffling of equivalent length. Falsified
  if the drop is within noise of the linear-shuffling drop, or (as already
  observed at pilot scale for thread attribution) a sub-dimension shows no
  drop at all.
- **H2 positive**: a measurable original-minus-counterfactual score gap,
  consistent in direction across stories/models. Falsified (per the
  blueprint's own explicit framing in §9 "Risks/Fallbacks") if the gap is
  near zero — which is *itself* a reportable finding (evidence of
  text-grounded rather than memorized reasoning), not a failed experiment.
  **Now tested at pilot scale (M4, §5.2)**: the headline AWT-F1 gap is ≈0 for
  4/5 stories, but this is a metric artifact (harmonic-mean zeroing when
  convergence is already 0 in both conditions), not evidence of no gap — the
  *sub-score* gaps are real and in two stories large (story_04's thread
  attribution collapses 1.000→0.044; story_05's relation score drops
  0.577→0.272 under the counterfactual/entity-renamed condition). Read
  together, this leans toward H2 positive (a real memorization-adjacent
  effect exists) but the evidence is pilot-scale (n=5) and mixed across
  stories, not a clean uniform gap.
- **H3 positive**: the graph pipeline's AWT-F1 (or a comparable metric) beats
  direct one-shot prompting on nonlinear/counterfactual conditions by a
  margin larger than run-to-run noise. Falsified if direct prompting matches
  or beats the graph pipeline — also explicitly pre-registered as a valid,
  reportable negative result in the blueprint. **Now tested at pilot scale
  (M3, §5.2)**: the direct baseline's relation_score beats the graph
  pipeline's on all 5 stories, and its headline AWT-F1 is strictly better on
  story_02 (0.713 vs. 0.289) and tied (both 0.000, both blocked by
  convergence) elsewhere — **H3 as originally stated is falsified at pilot
  scale**. This must be reported with an explicit fairness caveat: the direct
  baseline is only ever scored on a coarse before/after relation derived from
  its flat ordering (see `scripts/generate_direct_baseline_predictions.py`),
  which is structurally easier to get partial credit on than the graph
  pipeline's full 13-relation Allen vocabulary — so the comparison is
  generous to the baseline, not adversarial to the pipeline, and the finding
  is stronger for being generous rather than weaker.
- **H3a, revised**: the pipeline's own stage-wise diagnostics (relation /
  thread / convergence sub-scores) should show a concentrated, not uniform,
  failure distribution. This is **already partially confirmed** — pilot data
  shows a heavily concentrated failure in the convergence-detection stage —
  but the specific stage prediction (thread attribution/alignment) in the
  original hypothesis was wrong and should be revised in any future writeup
  to name convergence detection specifically.

**Explicit novelty caveat — partially re-verified (M2, 2026-09-03)**: a fresh
round of web searches re-checked the two load-bearing novelty claims. TLEX
(arXiv 2406.05265) was re-confirmed to still be detection-only ("any
inconsistencies discovered by TLEX need to be manually corrected") — no
retraction, update, or follow-up found that adds automatic correction. No
direct evidence was found of anyone using Allen's composition table
specifically as an auto-repair/constraint-satisfaction mechanism for
LLM-extracted temporal graphs — the PCR novelty claim survives this pass
(absence of evidence is not proof of absence, and this was not an exhaustive
systematic-review-grade search). One important **term-collision** was found
and must be explicitly distinguished in any writeup: "Graph Repairs with
Large Language Models: An Empirical Study" (arXiv 2507.03410) uses the same
phrase "graph repair" but for a structurally different problem — property-graph
schema/data-constraint violations repaired via *LLM reasoning*, with no
mention of Allen's interval algebra, temporal relations, or deterministic
constraint propagation. This is related-but-different prior art, not a prior
claim on this project's specific contribution, and should be cited as such to
preempt a reviewer conflating the two. Not yet done: a further targeted pass
specifically for competing verifier-guided/critic-guided temporal-reasoning
correction pipelines beyond what earlier `agent-reach`-driven research
already covered.

---

## 2. Related work landscape

Full detail lives in `docs/related_work.md` (read in full this session) and
`perplexity.md` (read in full this session, an external strategy pass over
the same idea). Summary table of the closest adjacent literatures and how
this project's claimed contribution differs:

| Cluster | Closest work | What it does | How this project differs |
|---|---|---|---|
| Direct predecessor | OpenReview `jogKc4OluB` | Single-chronology shuffled real biographies, AT/MT ordering | Genuinely multi-thread/flashback/fiction; counterfactual control |
| Chronology under known facts | "Do LLMs Understand Chronology?" (arXiv 2511.14214) | EM collapses with length; rank correlation more stable | Motivates AWT-F1's partial-credit design (`docs/metric.md`) |
| Allen relations + LLMs | QSTRBench (2605.18380), ChronoSense (2501.03040) | Test Allen-relation classification/composition in isolation | Embeds Allen relations inside a narrative comprehension task |
| Memorization control | ContraTable (2606.23667), CounterBench (2502.11008), Caliper (2606.04915), "Reasoning or Reciting?" (2307.02477) | Counterfactual perturbation on tables/causal QA | Same principle applied to narrative temporal ordering (not yet executed — see §5) |
| Graph repair for LLM-extracted temporal structure | TLEX (2406.05265) | Detects Allen-transitivity violations, no auto-correction (explicit future work in their paper) | PCR (this project) auto-corrects via composition-table vote + distance tie-break |
| Graph repair, different problem (term collision — found M2) | "Graph Repairs with Large Language Models: An Empirical Study" (2507.03410) | Repairs property-graph schema/data-constraint violations via LLM reasoning | No Allen algebra, no temporal relations, no deterministic constraint propagation — same phrase, different problem; must be cited to preempt reviewer conflation, not treated as prior art on this project's claim |
| Event-graph similarity metrics | CALLMSAE (2406.18449), Set-Aligning Framework (2404.01532), GEST (2305.12940), GRAIL (PMLR v267 2025) | Node-correspondence-free graph matching | AWT-F1 sidesteps correspondence via shared sentence-number IDs — narrower scope, explicitly flagged as a limitation, not solved generally |
| Narrative-to-graph pipelines | ChronoQA/Entity-Event RAG (ACL 2026.eacl-long.90), STAGE (2601.08510), Narrative Knowledge Weaver (2606.05724) | Extract-structure-evaluate pattern over narrative text | None target multi-thread temporal ordering or Allen relations specifically |
| Narrative structure benchmarks | LitVISTA/VISTA Space (ACL 2026.acl-long.1024) | Anchor-identification failures dominate on frontier models | Supports (partially) the "errors localize to a specific stage" framing, though this project's actual finding names a different stage (convergence, not anchor/attribution) |

**Gap flag — updated after M2 (2026-09-03)**: both items below were re-checked
via live web search this session. (1) TLEX/2026 successor auto-correction:
still not found — TLEX remains detection-only. (2) Allen composition table as
an LLM-graph repair mechanism: still not found. Both novelty claims survive
this pass, but the search was targeted, not systematic/exhaustive (no formal
database query across all venues) — a fully systematic search remains
recommended before final submission, especially given how fast this
literature is moving (multiple of the adjacent papers above are dated
2025-2026 already).

---

## 3. Method

### 3.1 Task and dataset

Five hand-authored stories (`data/stories/story_0{1..5}/`), each with:
- A shuffled, numbered-sentence passage (fed to the model).
- Gold structure: `events` (id, thread_id, time_expr, text), `threads`
  (id, label, granularity), `edges` (Allen-relation-labeled pairs), and
  `convergence_points` (cross-thread same-moment sentence groups).
- A structurally-identical **counterfactual twin** (`counterfactual.json`) —
  entity names substituted (verified via `scripts/check_coverage.py`'s
  structural-signature diff, confirmed run and passing), same gold graph
  shape, same relative ordering.

Story titles/structures (per `data/stories/manifest.json`): 3-4 threads each,
covering converging multi-thread narrative (`story_01`), flashback framing
(`story_02`), dual-direction/Memento-style threads (`story_03`), and
overlapping-duration stakeouts/shifts (`story_04`, `story_05`) — deliberately
chosen to stress different nonlinearity mechanisms.

**This is the "50–100 item pilot" scale explicitly recommended as step 2 of
`perplexity.md`'s "concrete next steps" (§5) before scaling up** — not yet
the full 1k+/subset target from §3.1.3 of that document. 5 stories is below
even the pilot floor perplexity.md suggests (50-100 items), so this pilot
should be read as a feasibility/methodology check, not a statistically
powered pilot.

### 3.2 Architecture / data flow

Two competing methods share one LLM client abstraction
(`pipeline/llm_client.py`: `complete(prompt, schema)`), backed by
`FeatherlessLLMClient` (an OpenAI-compatible endpoint, paid subscription,
`FEATHERLESS_API_KEY`) with `GroqLLMClient` as a free-tier alternative not
currently used for the saved results in `web/src/data/predictions/`. All
saved real-model predictions used **Qwen2.5-72B-Instruct** via Featherless
(`scripts/generate_real_predictions.py`, `MODEL` constant), temperature 0.

1. **Direct baseline** (`pipeline/direct_baseline.py`): one-shot prompt, ask
   for thread labels + full global order + convergence pairs in one call.
   **Implemented and unit-tested (`tests/test_pipeline.py`) but never run
   against real data** — see §5 gap list.
2. **Graph pipeline** (`pipeline/graph_pipeline.py`), 4+2 stages:
   1. Node extraction + thread attribution (LLM).
   2. Edge extraction — local Allen-relation pairs + candidate convergence
      groups (LLM). Candidate-format evolved through 3 versions this session
      (plain pairs → justified pairs → grouped multi-member candidates); see
      §5.3 for the empirical reasoning behind each change.
   3. **Path-Consistency Repair (PCR)** (`pipeline/graph_repair.py`, prior
      session segment): deterministic, zero-LLM-call. Detects Allen-relation
      transitivity violations against Allen's composition table
      (`metrics/allen_composition.py`) over every same-thread triangle in the
      predicted edge set; repairs to the vote-intersection relation closest
      (by Allen conceptual-neighborhood distance) to the model's original
      prediction; iterates to a fixed point; logs unrepairable conflicts
      (empty vote intersection) rather than guessing.
   4. Per-thread topological sort (deterministic).
   5. **Convergence-Order Consistency (COC)** (`pipeline/convergence_verification.py`,
      this session): deterministic, zero-LLM-call. Filters malformed/
      unknown-node/same-thread/duplicate candidates, then — the core new
      signal — treats each surviving cross-thread candidate as a point
      `(position_in_thread_a, position_in_thread_b)` using each thread's own
      already-computed chronological order (stage 4's input, available for
      free) and keeps only the largest mutually order-consistent subset per
      thread-pair via longest-increasing-subsequence (patience sorting,
      O(n log n)). This also incidentally resolves many-to-one collapse
      (two candidates sharing a target position cannot both survive a
      *strict* increase).
   6. Cross-thread alignment / final global order (deterministic, consumes
      COC's verified convergence points).

### 3.3 Evaluation metric

**AWT-F1** (`metrics/awt_f1.py`, full definition in `docs/metric.md`):
harmonic mean of three sub-scores — Allen-relation edge score, thread-
attribution accuracy, convergence-point F1. The harmonic mean returns exactly
0.0 if *any* sub-score is ≤0 — a deliberate design choice (not a bug) that
makes single-dimension failures maximally visible rather than averaged away,
which is precisely what surfaced the convergence-detection bottleneck this
session. Node correspondence between predicted and gold graphs is handled by
construction (shared sentence-number IDs), not by a Hungarian/optimal-
assignment matcher like CALLMSAE/Set-Aligning-Framework/GEST — `docs/metric.md`
already documents this as an explicit scope limitation, not an oversight.

**Addendum (2026-09-12): pooled (dataset-level) convergence F1.** Most
stories have only 1-2 gold convergence points, so per-story convergence_f1
is a high-variance statistic quantized to a handful of values (0, 0.4, 0.5,
0.57, 0.67, 1.0...) — it lands on exactly 0 whenever that tiny sample
misses, which then zeroes the harmonic-mean AWT-F1 headline regardless of
how good relation_score/thread_attribution (each computed over 30-50
edges/events — much more stable) were for that story. This made the
per-story headline number read as "total failure" in the web demo even when
two of three dimensions were fine. `metrics/awt_f1.py`'s new
`pooled_convergence_f1()` pools convergence pairs across every story
(namespaced by story id to prevent cross-story id collisions) before
computing precision/recall/F1 — standard micro-averaging practice for a
rare-event statistic with too few positives per group to score individually.
This does **not** replace the per-story `convergence_f1`/`awt_f1` (both
untouched, still used for diagnostic stage-wise scoring) — it's an
additional dataset-level view, used for both reporting and by the web demo's
sidebar (`web/src/lib/pooledConvergence.js` mirrors the Python function).
The web demo's score HUD was also re-ordered on this date: relation/thread/
convergence sub-scores are now the bold primary display, with AWT-F1
demoted to a small labeled secondary line ("harmonic mean, 0 if any score
above is 0") rather than presented as *the* verdict.

### 3.4 Where `agent-reach` fits

The only installed skill (`C:\Users\User\.claude\skills\agent-reach`) routes
web/code/social/dev/finance access through 15 platforms via `mcporter`/CLI
tools. Relevant routes for this project going forward: `search` (Exa web
search) and `dev` (`gh search`) for the fresh literature-verification pass
flagged in §1.4/§2; `web` (Jina Reader) for reading any newly found paper
pages. No social/career/finance routes are relevant to this project. This
skill has already been checked as the only one installed (no project-local
`.claude/skills/` directory exists) — no further skill-discovery work is
needed.

### 3.5 Design decisions and alternatives considered

- **PCR repair rule (vote-intersection + closest-by-distance tie-break) vs.
  majority-vote override**: chosen to stay maximally faithful to the model's
  own evidence-grounded prediction rather than blindly trusting whichever
  relation has the most supporting triangles — an alternative considered and
  rejected because it would silently discard model evidence that might be
  locally correct even when globally inconsistent.
- **COC's "leave out and log" on empty/contradictory candidates vs. forcing a
  guess**: chosen to match PCR's existing honesty-over-completeness pattern,
  and because a wrong forced guess would corrupt the downstream global sort
  in a way that's harder to detect than an admitted gap.
- **Group-based `members` convergence candidates (v3) vs. independently-
  guessed pairs (v1/v2)**: chosen after empirically observing that asking
  the model to guess one partner per flagged sentence caused systematic
  cross-thread mispairing; grouping "all sentences sharing this moment" in
  one judgment removes that failure mode (though a different, deeper
  recall problem remained — see §5.3).
- **Stopping prompt iteration after v3** rather than continuing to redesign
  the extraction prompt: decided (with explicit user sign-off in this
  session) after three independent prompt-format changes each fixed a
  distinct *structural* failure without closing the underlying *semantic*
  gap (interval-endpoint reasoning), which is evidence the bottleneck is a
  base-model reasoning limitation, not a prompt-engineering problem — see
  §5.3 for the concrete textual evidence. The alternative (keep iterating
  prompts) was judged likely to keep producing diminishing, non-generalizing
  fixes; the alternative *not* yet tried (a cheaper mitigation: explicitly
  prompting the model to reason about interval *endpoints* rather than
  matching literal timestamp strings) is logged as a candidate next step in
  §6, not dismissed.

---

## 4. Experimental plan

### 4.1 Experiments needed to support each claim

| Claim | Experiment | Data needed | Have it? |
|---|---|---|---|
| H1 | Linear (single-thread shuffled) vs. multi-thread/flashback AWT-F1, same event count | A linear-condition story set (blueprint's "Set A baseline", reusing the predecessor's Wikidata approach) | **No** — all 5 existing stories are already multi-thread/nonlinear; no linear control condition exists in this repo |
| H2 | Original vs. counterfactual AWT-F1, per story | Counterfactual predictions run through the pipeline | **Yes, pilot-scale (M4, §5.2)** — all 5 stories run via `scripts/generate_counterfactual_predictions.py`; headline `memorization_gap(awt_f1)` ≈0 for 4/5 (metric-artifact-masked), but sub-score gaps are real and large in 2/5 stories. n=5, one model — not statistically powered, reportable only as a pilot finding |
| H3 | Direct-baseline vs. graph-pipeline AWT-F1/Kendall's τ, same stories | Direct-baseline real-model runs | **Yes, pilot-scale (M3, §5.2)** — all 5 stories run via `scripts/generate_direct_baseline_predictions.py`; direct baseline beats the graph pipeline on relation_score for every story and on headline AWT-F1 where they differ. H3 as stated is falsified at pilot scale, with the caveat that the baseline is scored on a coarser before/after-only relation (generous to the baseline, so the finding is not an artifact of under-scoring it) |
| H3a | Stage-wise sub-score breakdown | Already-collected pipeline output | **Yes** — this is what §5 reports below |
| Model scaling / reasoning-mode effects | Same stories across model sizes/families | Multiple model API budgets | **No** — only Qwen2.5-72B-Instruct via Featherless has been used; Groq client exists but unused for saved results |
| Human baseline (optional, strengthens H2) | Small human study on original vs. counterfactual | Human annotators/time | **No** — not attempted, no infrastructure for it exists |

### 4.2 Metrics and protocol

AWT-F1 and its three sub-scores (§3.3) are implemented and unit-tested
(`tests/test_awt_f1.py`, `tests/test_allen_relations.py`). `perplexity.md`'s
proposed metric suite additionally calls for Exact Match, Kendall's τ, and a
memorization-gap statistic (`Score_original - Score_counterfactual`) — **EM
and Kendall's τ are not currently computed anywhere in this repo** (grep-
confirmed: no `kendall`/`exact_match` implementation found); the memorization-
gap statistic cannot be computed at all yet since no counterfactual
predictions exist (§4.1).

### 4.3 Compute/resource gaps

- **API budget**: one paid Featherless subscription (model used:
  Qwen2.5-72B-Instruct) plus a free-tier Groq key configured but unused for
  saved results. No frontier-model (GPT-5-class/Claude/Gemini) API access
  observed anywhere in this repo (`.env.local` was not read for this
  document — it may contain relevant keys not yet wired into any script; if
  so this should be confirmed and reflected here in the next update rather
  than assumed).
- **No compute cluster** — nothing in this repo suggests fine-tuning
  infrastructure (RQ6 in `perplexity.md`) is available; RQ6 should be treated
  as out of scope unless resources change.
- **No human-study infrastructure** — the optional human baseline
  (§3.4.3 of `perplexity.md`) is not currently feasible without external
  tooling/budget not present in this repo.

---

## 5. Current status

### 5.1 What exists (inventory, confirmed by directly reading the repo this
session, not from memory)

**Implemented and unit-tested (61/61 tests passing, confirmed via
`python -m pytest tests/ -q` this session)**:
- `metrics/allen_relations.py`, `metrics/allen_composition.py`,
  `metrics/awt_f1.py` — Allen-relation vocabulary, composition table, AWT-F1
  and its three sub-scores.
- `pipeline/graph_pipeline.py` — full 4-stage-plus-repair-plus-verification
  pipeline, wired end-to-end.
- `pipeline/graph_repair.py` (PCR) — deterministic transitivity repair.
- `pipeline/convergence_verification.py` (COC) — deterministic convergence-
  candidate verification, including this session's group-expansion addition.
- `pipeline/direct_baseline.py` — one-shot direct-prompting baseline, now run
  against real data (M3, §5.2) in addition to its existing fixture tests.
- `pipeline/llm_client.py` — `FeatherlessLLMClient`, `GroqLLMClient`,
  `FixtureLLMClient`.
- `pipeline/prompts.py`, `pipeline/schemas.py` — v3 (group-based) convergence
  candidate prompt/schema, current live version.
- `scripts/split_stories.py`, `scripts/check_coverage.py` — data-authoring
  and structural-integrity tooling; `check_coverage.py` confirms all 5
  original/counterfactual pairs are structurally identical twins. **Extended
  2026-09-03 (M6 scoped plan)** to also emit/validate a third `linear`
  variant per story (`_build_linear_variant`, `linear_matches_original`) —
  the same gold graph relabeled into chronological presentation order for
  the H1 comparison; verified against all 5 pilot stories.
- `metrics/significance.py` (**new 2026-09-03, M5/M8 scoped plan**) —
  `wilcoxon_test` (paired Wilcoxon signed-rank) and `bootstrap_ci` (story-
  level resampling), unit-tested in `tests/test_significance.py`; the
  statistical foundation for the scaled-up H1/H2/H3/PCR-COC comparisons.
- `requirements.txt` (**new 2026-09-03**) — first declared dependency
  manifest for this project (`requests`, `scipy`, `pytest`).
- `scripts/generate_predictions.py` — fixture-based synthetic-degradation
  demo (not a real-model run; useful for isolating PCR mechanics in
  isolation, explicitly documented as such in its own docstring).
- `scripts/generate_real_predictions.py` — real-model (Featherless/Qwen2.5-
  72B-Instruct) prediction generation, `"original"` variant.
- `scripts/generate_direct_baseline_predictions.py` (**new this session,
  M3**) — runs `pipeline/direct_baseline.py` against real data for all 5
  stories; writes `web/src/data/predictions/story_0{1..5}_direct.json`.
- `scripts/generate_counterfactual_predictions.py` (**new this session,
  M4**) — runs the real graph pipeline against the `"counterfactual"`
  variant for all 5 stories, computing `memorization_gap` against the
  existing original-variant results; writes
  `web/src/data/predictions/story_0{1..5}_counterfactual.json`.
- `scripts/rescore_predictions.py` — recomputes deterministic stages (PCR,
  COC, scoring) from already-saved LLM output without new API calls.
- `web/` — a working React + Three.js 3D visualization (Gold / Predicted /
  Repaired toggle, per-story picker), reading from
  `web/src/data/predictions/story_0{1..5}.json`.
- `data/stories/story_0{1..5}/{original,counterfactual}.json` — 5 stories,
  each with a structurally-validated counterfactual twin.
- `paper_draft.md` — a full pilot-stage academic draft written earlier this
  session, explicitly labeled "pilot-stage draft" at the top. **This document
  should be treated as existing prior work to reference, not extended
  further until this plan is reviewed** (per this session's explicit
  instruction).
- `docs/metric.md`, `docs/related_work.md` — design rationale and literature
  survey, both read in full this session.
- `thesis_blueprint_v2.pdf` — the original 4-page project blueprint (read in
  full this session): motivation, RQ1-3, H1-H3a, a worked example, dataset-
  construction plan (Sets A/B/C), the 4-stage method, evaluation plan,
  expected contributions, and an explicit risks/fallbacks section. This is
  the earliest and most authoritative statement of the project's original
  scope and should be treated as such going forward.
- `perplexity.md` — an external strategy/novelty-assessment pass over the
  same blueprint (read in full this session), source of the venue framing
  challenged in §1.3.

### 5.2 Experiments actually run, with actual results (no invented numbers)

**Staleness flag (2026-09-12): the table below predates the thread-
attribution leakage remediation** (character names removed from event-text
openings across all 5 stories to close a name-lookup shortcut the
`thread_attribution_accuracy=1.000` scores below were partly riding on —
see the Changelog entry for that fix). It also predates the pooled-
convergence metric addendum (§3.3) and the CRC pipeline-stage experiment
(§5.3a). It is kept here, not deleted, as the historical pre-remediation
record; the current, up-to-date picture is in §5.3a. A full reconciled
re-run of this table against the post-remediation dataset has not been done
yet (flagged in §5.4) — the numbers below should not be cited as current.

Real-model (Qwen2.5-72B-Instruct via Featherless) graph-pipeline results,
**original variant only**, current (v3 prompt/schema, post-PCR, post-COC)
state, confirmed from `web/src/data/predictions/story_0{1..5}.json` this
session:

| Story | relation | thread | convergence | **AWT-F1** | PCR repairs/conflicts | COC kept/dropped (raw candidate groups) |
|---|---|---|---|---|---|---|
| story_01 | 0.601 | 1.000 | 0.000 | **0.000** | 0/0 | 2/8 (from 3 raw groups) |
| story_02 | 0.533 | 1.000 | 0.133 | **0.289** | 0/0 | 13/37 (from 3 raw groups) |
| story_03 | 0.641 | 1.000 | 0.000 | **0.000** | 0/0 | 5/2 (from 3 raw groups) |
| story_04 | 0.517 | 1.000 | 0.000 | **0.000** | 73/58 | 6/15 (from 5 raw groups) |
| story_05 | 0.577 | 1.000 | 0.000 | **0.000** | 10/23 | 19/97 (from 7 raw groups) |

**Interpretation, stated plainly**: thread attribution is solved at this
pilot scale (1.000 across all 5 stories). Relation extraction is moderate
(0.52-0.64) and PCR is doing real, nontrivial work on story_04/story_05 (73
and 10 repairs respectively) but that work does not by itself fix the
headline AWT-F1 because convergence detection is failing almost everywhere.
Convergence-point recall is the dominant, load-bearing failure mode: 4 of 5
stories score exactly 0.000 convergence-F1, which zeroes AWT-F1 for those 4
stories regardless of the other two sub-scores' quality. This is the central
empirical finding of this session's work.

**M3 — direct baseline vs. graph pipeline, real data (2026-09-03).** Ran
`scripts/generate_direct_baseline_predictions.py` (new this session) against
all 5 stories' `"original"` variant via Featherless/Qwen2.5-72B-Instruct.
This is the first time `pipeline/direct_baseline.py` has ever been run
against real (non-fixture) data. First run scored 0.000 on every sub-score
for every story; inspecting `story_01_direct.json` found the model returning
bare-number ids ("10" instead of "s10") because `direct_baseline_prompt`
(`pipeline/prompts.py`) never actually specified the required id format
(unlike `node_extraction_prompt`, which does). Fixed by editing the prompt to
require "s"-prefixed ids explicitly, plus a defensive `normalize_id` in the
new script as a safety net. Final results, post-fix, with the graph
pipeline's original-variant numbers repeated alongside for direct comparison:

| Story | Direct relation | Direct thread | Direct convergence | **Direct AWT-F1** | Graph relation | Graph thread | Graph convergence | **Graph AWT-F1** |
|---|---|---|---|---|---|---|---|---|
| story_01 | 0.873 | 1.000 | 0.000 | **0.000** | 0.601 | 1.000 | 0.000 | **0.000** |
| story_02 | 0.871 | 0.944 | 0.500 | **0.713** | 0.533 | 1.000 | 0.133 | **0.289** |
| story_03 | 0.910 | 0.917 | 0.000 | **0.000** | 0.641 | 1.000 | 0.000 | **0.000** |
| story_04 | 0.694 | 1.000 | 0.000 | **0.000** | 0.517 | 1.000 | 0.000 | **0.000** |
| story_05 | 0.642 | 0.926 | 0.000 | **0.000** | 0.577 | 1.000 | 0.000 | **0.000** |

**Interpretation, stated plainly**: the direct baseline's relation_score beats
the graph pipeline's on all 5/5 stories, and its headline AWT-F1 strictly
beats the graph pipeline's wherever they differ (story_02: 0.713 vs. 0.289),
tying (both 0.000) elsewhere because convergence recall is near-zero for
both methods. **H3 as originally stated (graph pipeline beats direct
prompting) is falsified at this pilot scale** — this is exactly the kind of
valid, pre-registered negative result the blueprint's own "Risks/Fallbacks"
section anticipated, not a failed experiment. The one load-bearing fairness
caveat: the direct baseline is only ever scored on a coarse before/after
relation derived from its flat `global_order` (see
`derive_edges_from_order` in the new script's docstring), because the method
structurally never produces a full Allen relation — it cannot ever score
>0 on a gold edge whose true relation is e.g. "overlaps" or "during". This
scoring choice is *generous* to the baseline (any consistently-ordered pair
gets full before/after partial credit), so the finding that it still wins on
relation_score is not an artifact of unfairly deflating the graph pipeline —
if anything the comparison understates how much simpler the winning method
is.

**M4 — counterfactual variant through the real graph pipeline (2026-09-03).**
Ran `scripts/generate_counterfactual_predictions.py` (new this session)
against all 5 stories' `"counterfactual"` variant via the real graph
pipeline — the first time this variant has ever been run through the
pipeline (previously validated structurally only, via `check_coverage.py`,
never scored). Hit a real `KeyError: 'node_j'` crash in
`pipeline/graph_repair.py`'s `repair_edges` on story_01's counterfactual run,
because a real model-returned edge object was missing the `node_j` key and
the filter used direct dict indexing. Fixed by switching to `.get()` for
`node_i`/`node_j` and adding an `allen_relation in RELATIONS` vocabulary
check — the same category of defensive gap already named in this project's
own PCR/COC design docs, now caught for real by exercising a code path real
counterfactual-variant output had never hit before. Verified via
`python -m pytest tests/ -q` (61/61 still passing) before rerunning. Results,
with `memorization_gap` = original − counterfactual per sub-score (positive
= worse on the counterfactual, i.e. evidence of a memorization-adjacent
effect):

| Story | Orig. relation | CF relation | Δrelation | Orig. thread | CF thread | Δthread | Orig. conv | CF conv | Δconv | Orig. AWT-F1 | CF AWT-F1 | ΔAWT-F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| story_01 | 0.601 | 0.580 | +0.021 | 1.000 | 1.000 | +0.000 | 0.000 | 0.000 | +0.000 | 0.000 | 0.000 | +0.000 |
| story_02 | 0.533 | 0.492 | +0.041 | 1.000 | 0.972 | +0.028 | 0.133 | 0.133 | +0.000 | 0.289 | 0.284 | +0.005 |
| story_03 | 0.641 | 0.641 | +0.000 | 1.000 | 1.000 | +0.000 | 0.000 | 0.000 | +0.000 | 0.000 | 0.000 | +0.000 |
| story_04 | 0.517 | 0.446 | +0.071 | **1.000** | **0.044** | **+0.956** | 0.000 | 0.000 | +0.000 | 0.000 | 0.000 | +0.000 |
| story_05 | 0.577 | 0.272 | **+0.305** | 1.000 | 0.907 | +0.093 | 0.000 | 0.000 | +0.000 | 0.000 | 0.000 | +0.000 |

**Interpretation, stated plainly — this is a genuine, important
methodological finding, not just a data point.** The headline
`memorization_gap(awt_f1)` is ≈0 for 4 of 5 stories, which on its own would
read as "no memorization gap, H2 negative/falsified." That reading is
**wrong**: it's a floor effect of AWT-F1's harmonic-mean design — when
convergence_f1 is already 0 in *both* the original and counterfactual
condition (as it is in 4/5 stories, per §5.2's convergence finding), the
headline metric is 0 either way and the gap is mathematically forced toward
0 regardless of what happens to relation/thread scores underneath. The
sub-score deltas tell a different, real story: **story_04's thread
attribution accuracy collapses from a perfect 1.000 to 0.044** under the
counterfactual (entity-renamed, structurally-identical) condition, and
**story_05's relation score drops by 0.305** (0.577→0.272) — both far larger
than story-to-story noise seen elsewhere in this table (most Δrelation/Δthread
values are ≤0.07). This is evidence leaning toward **H2 positive** (a real
effect exists that looks memorization-adjacent — the model does substantially
worse when the same structure is dressed in unfamiliar names/details) but the
evidence is uneven (3/5 stories show only small deltas) and pilot-scale
(n=5, one model), so it should be reported as a suggestive pilot finding, not
a confirmed effect. **The actionable methodological conclusion**: AWT-F1's
harmonic mean, while valuable for surfacing single-dimension failures (its
original design intent, confirmed in §5.2), is the wrong lens for measuring
memorization gaps once one dimension is already saturated at the floor in
both conditions being compared — any H2 analysis must be done at the
sub-score level, not the headline AWT-F1 level, and this limitation should be
stated explicitly in any writeup rather than silently working around it.

### 5.3 Diagnostic history (why convergence detection fails) — already
investigated this session, not yet resolved

Three independent candidate-format redesigns were tried, in order, each
motivated by inspecting the previous version's concrete failure mode:

1. **v1** (plain `[node_i, node_j]` pairs, no justification): noisy —
   produced malformed/same-thread/duplicate candidates that COC's structural
   filters correctly rejected, but true recall was not measurably better.
2. **v2** (`{node_i, node_j, shared_detail}`, prompt enumerating 4 signal
   types): fixed the noise problem (candidates became well-formed and
   grounded), but revealed **cross-thread mispairing** — the model correctly
   flags both true convergence anchors individually but pairs each with the
   wrong partner sentence.
3. **v3** (`{members: [...], shared_detail}` groups, two-pass prompt — flag
   signal sentences, then group all sentences sharing one instant): fixed the
   mispairing mechanism (grouping avoids forcing an independent per-sentence
   guess), but revealed a different, deeper problem: **surface timestamp-
   string matching instead of true interval-endpoint reasoning** — e.g. the
   model over-groups sentences that share a literal token like a stated start
   time, but fails to recognize that one interval's stated *end* is the same
   instant as another sentence's explicit timestamp (concrete examples:
   story_04's split-bucket s2/s6 case, story_05's 13-member over-grouping
   case, both inspected directly in the live model output this session).

**Conclusion reached and acted on this session**: since three structurally
different prompt redesigns each fixed a distinct *structural* failure without
closing the underlying *semantic* gap, the bottleneck is most likely a
Qwen2.5-72B-Instruct interval-endpoint/duration-reasoning limitation, not a
prompt-format problem — and prompt iteration was deliberately stopped (with
explicit user sign-off) in favor of documenting this as a finding. **This
conclusion has not been tested against a different, stronger model** — it
remains possible that a frontier model (GPT-5-class/Claude/Gemini) would not
show the same failure, which would point back toward a base-model-capability
explanation rather than a task-difficulty explanation. That comparison has
not been run (§4.3 resource gap) and is flagged as the single highest-value
next experiment if any additional model budget becomes available.

### 5.3a CRC (Convergence Recall Critique) — a candidate pipeline stage,
tested this session, result inconclusive at current scale (2026-09-12)

**What it is**: `pipeline/graph_pipeline.py`'s `run_graph_pipeline(...,
use_recall_critique=True)`, opt-in (default `False`, so nothing already
reported was silently changed). After the normal edge-extraction call
returns its convergence candidates, one additional LLM call shows the model
the full passage plus what it already flagged and asks explicitly for
cross-thread same-moment pairs it *missed* — a recall-focused critique pass,
motivated by a literature finding (agent-reach/Exa research this session):
no prior work frames a self-critique pass around recall-of-omissions
specifically (the Self-Refine/Reflexion/CRITIC literature all targets
correctness of existing output). New candidates are merged into the same
pool COC already verifies, so COC's deterministic order-consistency filter
is unchanged and remains the precision backstop. Implementation: 2 new tests
in `tests/test_pipeline.py` demonstrate the mechanism deterministically via
`FixtureLLMClient` (no live LLM needed to verify correctness); reviewed
clean by `python-reviewer`/`react-reviewer` (two trivial LOW fixes applied).

**Live ablation, same model (Groq gpt-oss-120b, since Featherless's
subscription lapsed mid-session — billing issue, not a methodology choice),
same stories, only the CRC flag toggled**:

| Stories pooled | No-CRC recall | CRC recall | No-CRC precision | CRC precision | No-CRC F1 | CRC F1 |
|---|---|---|---|---|---|---|
| story_01 + story_03 (n=2) | 0.333 | 0.333 (tied) | 0.143 | 0.091 (worse) | 0.200 | 0.143 (worse) |
| story_01-04 (n=4) | 0.333 | **0.500** | 0.083 | 0.091 | 0.133 | **0.154** |

**Honest interpretation, including a self-correction**: my first read of the
n=2 result (story_01 alone showed 0.000→0.200) was reported as a "clean win"
before the paired no-CRC baseline existed. Once the fair baseline was built,
pooling story_01+story_03 showed recall exactly tied and precision *worse*
with CRC — the story_01 gain was cancelled out by story_03's baseline
happening to find its one gold pair on its own (see the non-determinism
finding below), which CRC's independent run of the same edge-extraction call
did not reproduce. That correction was reported to the user directly. Adding
story_02 and story_04 (n=4, 6 total gold pairs) shifted the picture again,
now positive: recall 0.333→0.500, F1 0.133→0.154. **Neither reading is
trustworthy on its own** — the sample is still far too small (6 pooled gold
pairs) for the direction to mean anything without a significance test
(`metrics/significance.py`'s Wilcoxon/bootstrap tooling, built for exactly
this, not yet run against CRC). The honest status is: *a plausible
mechanism, one inconclusive small-sample ablation, not a demonstrated
result* — do not cite either the n=2 or n=4 number as "CRC works" or "CRC
doesn't work" in any writeup.

**A second, independent finding surfaced by this ablation**: hosted LLM
inference is not run-to-run deterministic even at temperature 0. story_03's
no-CRC baseline scored convergence_f1=0.333; a fresh CRC run of the
*identical* edge-extraction prompt (CRC can only add candidates, never
remove) scored 0.000 on the same story. Since CRC cannot subtract
candidates, this gap can only be explained by the shared first-pass call
itself returning different raw output across two separate API calls
(server-side batching effects on Groq's hosted stack, most likely). This
means **any future single-run pilot-scale comparison on a hosted API is at
real risk of reading noise as signal** — reinforcing, from direct evidence
now rather than just statistical principle, why the N=20 scale-up plan
already calls for paired significance testing rather than eyeballing one run
per condition.

**Not yet done**: significance testing on the n=4 CRC data; CRC run against
story_05 (excluded from the web demo, §6); a matched-passage design (fork
CRC-on/CRC-off from the *same* edge-extraction output rather than two
independent LLM calls, which would isolate CRC's own effect from first-pass
run-to-run noise — a cleaner ablation than what was run here, flagged as the
right fix before drawing any real conclusion).

### 5.3b Scoring bugs found and fixed, and what they did to the H3 result
(2026-09-12)

Five defects were found in the evaluation and pipeline. Three were scoring
bugs, and **all three biased the same direction -- against the graph pipeline
and in favour of the direct baseline** -- so the previously reported "direct
prompting beats the graph pipeline" (§5.2, §1.4) was substantially a
measurement artifact rather than a finding.

1. **The two methods were scored on structurally different outputs.** The
   direct baseline is scored by deriving a before/after for every gold pair
   from its global ordering, giving it 100% coverage of gold edges by
   construction. The graph pipeline was scored only on the explicit Allen
   edges it chose to emit (20-46% of gold edges), with every un-emitted pair
   scoring 0.0 -- even though the pipeline also produces a complete
   `global_order` that determines those pairs, which scoring discarded.
   Measured on the edges each method actually commits to, the pipeline was
   already the more accurate of the two (story_01 0.926 vs 0.819). Fixed by
   scoring both on their full output.
2. **Reversed-orientation edges were compared against the wrong label.**
   "B after A" asserts exactly what gold's "A before B" does, but scored
   0.333 instead of 1.0. The baseline never hit this path, since
   `derive_edges_from_order` emits pairs in gold's own orientation. Fixed with
   an inverse map derived from the endpoint-rank table.
3. **The PCR ablation was structurally always 0.0.** Raw candidate groups
   passed to `convergence_f1` hit `frozenset(dict)`, which iterates the dict's
   KEYS, so every group collapsed to the same meaningless set. Every
   `repair_delta` ever reported measured nothing.

Two further pipeline bugs: COC's longest-increasing-subsequence tie-break
evicted already-correct convergence anchors when a new candidate arrived, and
`starts`/`started-by` were treated as strict precedence in the per-thread sort
although they assert simultaneous starts.

A sixth, process-level defect: the earlier leakage remediation edited the
GENERATED `data/stories` files rather than the `data/authoring` sources they
are rebuilt from, so the next `split_stories.py` run silently reverted every
fix. Confirmed by observation -- stories were back over threshold. Remediation
is now applied at the source.

### 5.3c Convergence was never a model failure -- it was the metric
(2026-09-12)

Convergence F1 read 0.000 almost everywhere. The cause is annotation
completeness, not model capability: story_06 contains **65** cross-thread
pairs that genuinely share a boundary instant, while gold annotates the **3**
narratively salient ones. Exact set match therefore scored a model *wrong*
for correctly identifying a true simultaneity nobody annotated -- the pipeline
proposed [s14,s32] (both touch t=40) and [s21,s26] (both touch t=45), both
genuinely simultaneous, both counted as false positives.

This is a named, documented failure mode. Sparse temporal annotation
conflating "no relation" with "unannotated" is precisely why TB-Dense
(Cassidy et al., ACL 2014) exists, and TempEval-3's temporal awareness
(UzZaman & Allen, ACL 2011) addresses it by scoring precision against the
transitive closure of gold, so derivable-but-unannotated predictions count as
correct rather than wrong.

Adopted as two separate measurements, deliberately not combined:
`convergence_precision_vs_pool` (of what was proposed, how much is genuinely
simultaneous, judged against every valid simultaneity derivable from the
intervals, with a TempEval-3-style reduction dropping trivial shared
story-frame anchors) and `convergence_recall_salient` (of the annotated
salient moments, how many were found). On story_06 this immediately exposed
signal the old metric destroyed: graph pipeline 0.400 precision vs direct
baseline 0.200, where both previously read 0.000.

The headline aggregate was also replaced. A convergence estimate from 1-3
annotated items was annihilating a ~46-edge relation estimate and a 36-45
event thread estimate through the harmonic mean, guaranteeing 0.000.
`awt_core` is the harmonic mean of the two well-sampled sub-scores, with
convergence reported alongside; `awt_f1_legacy_harmonic` is retained so prior
figures stay reproducible and this revision is auditable. Aggregating
incommensurable sub-scores this way is criticised directly in the
benchmark-methodology literature (arXiv:2112.01342; Colombo et al.,
arXiv:2202.03799).

### 5.3d Benchmark validity: the dataset could not measure what it claimed
(2026-09-12)

In stories 1-5, **48% of gold edges are before/after**, and the Allen-distance
partial credit is generous to before/after guesses on the rest. Consequence: a
method that cannot express interval relations at all -- one that merely SORTS
events, which is exactly the direct baseline's structural limit -- scores
**0.849** on this dataset. The benchmark could not distinguish interval
reasoning from sorting, and the direct baseline was already operating at that
structural ceiling.

Two new stories address this, built by a new toolchain
(`scripts/build_story.py`) in which the author supplies each event's real
interval and which pairs a reader could infer a relation between, and every
gold label is DERIVED via `relation_from_intervals`. A gold graph built this
way cannot disagree with the timeline its prose describes, and the relation
distribution becomes a design parameter rather than an accident.

- **story_06 "Signal Loss"** -- 36 events, 4 threads, before/after 4.3%,
  order-only ceiling 0.754, all 13 relations covered.
- **story_07 "Tide Watch"** -- 45 events, 5 threads, before/after 3.7%, all 13
  relations covered.

Both carry threads by pronoun, role noun, and location rather than name;
trivial lexical-baseline thread accuracy is 0.000 on story_06 (vs up to 0.78
in the original set).

The derivation tool also surfaced a modelling bug in stories 1-5: Allen's
algebra is undefined over zero-length intervals, yet those stories contain
instantaneous events whose hand-typed relations were therefore never
well-defined.

### 5.3e H3 after the fixes: no reliable separation, and a retracted claim
(2026-09-12)

Same-model (gpt-oss-120b) head-to-head on relation_score, both arms scored on
their full output:

| Story | before/after share | direct | graph | winner |
|---|---|---|---|---|
| story_01 | 85% | 0.819 | 0.851 | graph |
| story_02 | 75% | 0.875 | 0.808 | direct |
| story_03 | 77% | 0.910 | 0.863 | direct |
| story_06 | 4% | 0.699 | 0.739 | graph |
| story_07 | 4% | 0.710 | 0.630 | direct |

**Retraction of an intermediate claim made during this session.** After the
scoring fixes but before the model confound was removed, a perfect
correlation appeared between a story's before/after share and which method
won, and was reported as the session's cleanest result. It did not survive:
re-running stories 1-3 on the same model as their baselines flipped story_01
to the pipeline, and story_07 -- interval-rich, where the hypothesis predicts
a pipeline win -- went to the baseline. The pattern was partly an artifact of
the very model confound it was meant to control for. Current state is **direct
3 / graph 2 with no predictive relationship to relation balance**, which is a
weaker and less tidy claim than the one briefly recorded.

What the fixes did establish, and which does hold: the margins are now small
(~0.05 rather than ~0.5), the pipeline is more accurate on the pairs it
commits to, and it wins outright on 2 of 5 stories -- none of which was
visible under the buggy scoring.

Thread attribution is the pipeline's clearest current weakness, and
referential indirection hurts it badly: story_06 0.444 and story_07 0.556,
against baselines of 0.861 and 0.400 respectively.

**Not yet done**: story_04 has no same-model graph run (Groq daily quota
exhausted mid-session), so it is excluded from the table above; n=5 is far too
small for any of this to be significance-tested, and
`metrics/significance.py` has still never been run against it.

### 5.4 What's missing to reach a submittable paper (honest list)

1. **Scale**: 5 stories vs. blueprint's 3-4k passage target (or even
   perplexity.md's own 50-100 item pilot floor). Nothing in this repo has
   been tested for statistical significance because there isn't enough data
   to compute it meaningfully.
2. **H1 untested**: no linear/single-thread control condition exists to
   compare against.
3. **H2 pilot-tested, not fully resolved (M4, §5.2)**: real counterfactual
   runs now exist for all 5 stories. The headline metric shows ≈0 gap (a
   metric artifact, see §5.2), and the sub-score-level evidence is uneven —
   2/5 stories show a large gap, 3/5 show a small one. Needs more stories
   and/or models before this is more than a suggestive pilot finding, and the
   analysis must be redone at sub-score granularity, not headline AWT-F1.
4. **H3 pilot-tested (M3, §5.2)**: direct-vs-graph comparison now exists for
   all 5 stories and falsifies H3 as originally stated at pilot scale (direct
   prompting's relation_score wins on every story). Still needs more stories/
   models to move beyond a pilot-scale claim, and the coarse before/after-only
   baseline-scoring caveat (§5.2) must be stated in any writeup.
5. **Single model**: only Qwen2.5-72B-Instruct has been used for real
   predictions; no scaling or cross-family comparison exists.
6. **EM / Kendall's τ metrics** from `perplexity.md`'s proposed evaluation
   protocol are not implemented anywhere in this repo.
7. **Novelty claims not freshly re-verified** this session (§1.4/§2) — a
   literature-search pass using `agent-reach` should happen before any
   submission-level novelty claim is finalized.
8. **`.env.local` not inventoried** this session — should be checked (without
   printing secret values) to confirm exactly which API keys/models are
   actually available versus assumed.
9. **`Nonlinear Temporal Reasoning.sty`** (a LaTeX style file in the project
   root) exists but its content/purpose was not inspected this session —
   likely a formatting template for a specific target venue or thesis
   template; should be opened before any paper-writing phase to know what
   format constraints it implies.
10. **CRC (§5.3a) needs a matched-passage ablation and significance testing**
    before its recall effect can be claimed either way — current n=4/6-pair
    pooled result is directionally positive but not statistically
    distinguishable from the hosted-API run-to-run noise also found this
    session. The cleaner design (fork CRC-on/CRC-off from one shared
    edge-extraction call rather than two independent ones) is not yet built.
11. **§5.2's per-story table is pre-leakage-remediation and pre-CRC** — a
    reconciled re-run against the current dataset/pipeline has not been done
    (flagged at the top of §5.2 itself).

### 5.5 Risk list (honest)

- **Technical risk**: convergence detection may be a genuine model-capability
  ceiling that no amount of pipeline engineering (further COC refinement,
  more PCR-style repair) can fully close — the repair/verification stages
  built this session can only work with *some* correct signal from the LLM;
  if recall stays near zero, there is nothing to verify. Mitigation path
  (untried): test whether a stronger/frontier model has materially better
  raw convergence recall before concluding this is a fundamental limit.
- **Novelty risk**: the PCR/COC contribution's novelty rests on TLEX (arXiv
  2406.05265) not having added auto-correction since the last check, and on
  no other 2025-2026 paper independently having done the same composition-
  table-as-repair idea. **Re-checked this session (M2, §1.4/§2)** via targeted
  web search — both claims survive, and a term-colliding-but-different paper
  (2507.03410) was found and must be distinguished in any writeup. This was a
  targeted pass, not a systematic/exhaustive one; a fully systematic search
  is still recommended before final submission.
- **Metric-design risk (new, found this session via M4)**: AWT-F1's harmonic
  mean, useful for surfacing single-dimension failures, produces a floor
  effect that masks real sub-score gaps whenever one dimension (here,
  convergence) is already 0 in both conditions being compared. Any H2
  memorization-gap analysis must be reported at the sub-score level; the
  headline metric alone is actively misleading for this specific comparison.
- **Timeline/scale risk**: closing the gaps in §5.4 (linear control set,
  counterfactual runs, direct-baseline runs, multi-model runs) is a
  significant amount of additional data-authoring and API-budget work, not a
  quick follow-up. The milestone plan (§6) sequences this realistically
  rather than assuming it can all happen at once.
- **Scope risk**: given the mismatch between the blueprint's original A*-
  venue ambition and the current pilot's actual scale (§1.3), there is a real
  risk of over-investing in paper-submission polish before the underlying
  experiments (H1/H2/H3) actually exist. The milestone plan treats "decide
  the venue/scope question" as an early, explicit checkpoint rather than an
  implicit assumption.

---

## 6. Milestone plan

Each milestone has a concrete exit criterion (not "X working") and a
checkpoint marker where human review is expected before continuing.
**Time estimates below M1.1 assume a 3-person team over a ~16-week (~4
month) window from 2026-09-04 to defense, not solo work** — see the
week-by-week timeline in the thesis-plan document (`thesis_plan.html` at the
project root, open directly in a browser — not published as a hosted link;
see the Changelog's 2026-09-04/09-05 entries) for the actual schedule; the
milestone table here stays the source of truth for exit criteria and
completion status.

| # | Milestone | Exit criterion | Est. time | Checkpoint? |
|---|---|---|---|---|
| M0 | ~~This document reviewed~~ **Superseded** | User instructed ("do everything you can" toward assessing A*-tier viability) to proceed past this checkpoint before a formal review; treated as explicit authorization to continue to M2-M4 | — | Superseded 2026-09-03 |
| M1 | Venue/scope decision (solo A*-tier framing) | Explicit decision recorded in this file's changelog | — | **Superseded 2026-09-04 (M1.1)** — the solo full-A*-scale/ARR-cycle decision below is kept for history only; see M1.1 for the current scope. |
| M1.1 | Thesis scope decided | Explicit decision recorded in this file's changelog | — | **Done (2026-09-04)** — user pivoted the project to an **undergraduate thesis, 3-person team, ~4-month timeline to defense, N=20 dataset scale retained, thesis-only target (external paper submission not a current goal)**. See §1.3 for updated venue framing. |
| M2 | Fresh novelty verification | `agent-reach`/web search pass re-confirms (or corrects) the TLEX/composition-table-as-repair claim and the other headline novelty claims in §1.2/§2; results recorded in this file, not silently assumed | 1 session | **Done (2026-09-03)** — TLEX still detection-only; no prior composition-table-as-repair work found; term-collision paper 2507.03410 found and distinguished (§1.4/§2). Targeted, not exhaustive. |
| M3 | Direct-baseline real-model run | `pipeline/direct_baseline.py` run against all 5 existing (original) stories via Featherless; direct-vs-graph AWT-F1/relation/thread/convergence numbers recorded side by side in this file — first real H3 data point, even at pilot scale | 1 session | **Done (2026-09-03)** — see §5.2. H3 as stated falsified at pilot scale; found and fixed a real id-format prompt bug in the process. |
| M4 | Counterfactual real-model run | `scripts/generate_counterfactual_predictions.py` runs the `counterfactual` variant for all 5 stories; original-vs-counterfactual AWT-F1 gap computed and recorded — first real H2 data point | 1 session | **Done (2026-09-03)** — see §5.2. Headline gap ≈0 masks real sub-score gaps (metric-artifact finding); found and fixed a real `KeyError` crash in PCR in the process. |
| M5 | Second model + significance tooling | `metrics/significance.py` (Wilcoxon + bootstrap CI) built and tested; `GroqLLMClient`/`openai/gpt-oss-120b` wired as a secondary cross-model robustness condition | Weeks 2-9 (team timeline) | No |
| M6 | Linear-condition control set + full data scale-up | Dataset scaled from 5 to 20 nonlinear stories (original/counterfactual/linear each); `linear` variant is a presentation-order relabeling of each story's own gold graph, not a separately authored story (see scoped-plan note below) | Weeks 2-9 (team timeline) | No |
| M7 | Pilot-scale H1/H2/H3 result set complete | Superseded by the M5/M6 scoped plan above | — | Superseded 2026-09-03 |
| M8 | Full-scale statistical validation | `scripts/statistical_analysis.py` reports Wilcoxon signed-rank + bootstrap CI for H1/H2/H3 and the PCR/COC repair effect, N=20-25, paired by story | Weeks 9-10 (team timeline) | **Yes** |
| M9 | Thesis writing begins | Only after M8 — `paper_draft.md`/`PLAN_AND_STATUS.md` §3 revised (not restarted) to incorporate real H1/H2/H3 numbers in place of the current single-condition pilot table, feeding the thesis chapters (Intro, Related Work, Method, Experiments, Results, Discussion, Conclusion) | Weeks 10-15 (team timeline) | **Yes — explicit "begin writing" checkpoint** |

**Immediately next**: M0-M4 are done; M1.1 (thesis scope) is decided
(2026-09-04): 3-person team, ~4-month timeline, N=20 retained, thesis-only
target. The concrete M5/M6/M8 scope below was originally designed for a solo
~4.5-week ARR push (2026-09-03, plan file `goofy-foraging-puzzle.md`) and has
been rescheduled against the 3-person/~16-week team timeline instead — the
content (N=20/hybrid-authoring/linear-variant/Groq-secondary-model/
statistical-protocol) is unchanged and still valid, only the pacing and the
prior deadline pressure are superseded:

**Scoped plan for M5/M6/M8 (content decided 2026-09-03, rescheduled
2026-09-04 against the ~16-week team timeline; see the thesis-plan document
at `thesis_plan.html` (project root) for the week-by-week breakdown):**

- **Target N**: 5 → **20 nonlinear stories** (original + counterfactual +
  linear per story = 60 passages, 20 shared gold graphs). 15 new stories via
  a **hybrid authoring method** (user's explicit choice via AskUserQuestion,
  over fully-manual or fully-LLM-generated): a human writes a short outline
  (threads, key events, intended edges/convergence points, target Allen-
  relation mix), an LLM drafts passage text + a candidate gold graph from it,
  a human then reviews/corrects the gold graph before it's added — keeping a
  human in control of ground-truth validity (the part AWT-F1's entire design
  depends on) while going faster than the fully-manual method used for the 5
  pilot stories.
- **H1 no longer needs new stories.** `pipeline/graph_pipeline.py`'s
  `topological_sort_per_thread` + `align_convergence_points` already compute
  a gold-consistent chronological order from any story's `edges`/
  `convergence_points`. `scripts/split_stories.py` now emits a third variant,
  `linear.json`, per story: the same gold graph, presented in that
  chronological order instead of the shuffled/interleaved order, with every
  event/edge/convergence-point id relabeled via `id_map_from_original` to
  match the new sentence order (ids double as sentence numbers — see
  `pipeline/prompts.py`'s node-correspondence convention). `linear_matches_
  original()` in `scripts/check_coverage.py` verifies this relabeling is
  exact — the linear condition is a presentation-order twin of `original`,
  never a structurally different graph. **Built and verified 2026-09-03**:
  regenerated for all 5 pilot stories, `check_coverage.py` passes including
  the new relabeling check; `tests/test_split_stories.py` covers the
  relabeling logic directly. A `python-reviewer` pass caught a real
  determinism bug in the reused `topological_sort_per_thread` (its
  per-thread node set iterated in Python's randomized string-hash order
  before being fed to `TopologicalSorter`, so ties — event pairs with no
  precedence edge between them — could get a different relative order on
  each script run, since `graph_pipeline.py` is otherwise used only for
  predictions where this never mattered). Fixed by sorting ids before adding
  them to the sorter (`pipeline/graph_pipeline.py`); `linear.json` for all 5
  pilot stories was regenerated after the fix and still validates.
- **Models**: `Qwen/Qwen2.5-72B-Instruct` (Featherless, paid) stays primary.
  `openai/gpt-oss-120b` (Groq, free tier, already wired via
  `GroqLLMClient`) is added as a secondary cross-model robustness check —
  **updated 2026-09-04**: with a 3-person team and ~4 months, the prior
  "reduced scope, cut if tight" hedge on the Groq run no longer applies;
  Groq's free-tier rate limits remain a practical constraint on pacing but
  are no longer treated as an at-risk line item likely to be dropped.
- **Human baseline**: **cut**, explicit decision — recruiting/paying/
  coordinating human raters is still out of scope for this thesis (no budget
  or IRB-style infrastructure exists in this repo), independent of team size.
  Stated as future work.
- **Statistical protocol**: `metrics/significance.py` (**built and tested
  2026-09-03**, `tests/test_significance.py`) provides `wilcoxon_test`
  (paired Wilcoxon signed-rank, chosen for no normality assumption at
  N=20-25) and `bootstrap_ci` (10,000 resamples, story-level, for effect-size
  context). Planned comparisons, all paired by story: H2 (original vs.
  counterfactual, headline AWT-F1 **and each sub-score** — the M4 pilot
  finding was that sub-score-level analysis is required, since the harmonic
  mean's floor effect masks real gaps at the headline level, §5.2); H3
  (direct baseline vs. graph-pipeline `relation_score`); H1 (linear vs.
  nonlinear `original`, newly enabled by the linear-variant insight above);
  the PCR/COC repair effect (`awt_f1_scores` vs. `awt_f1_scores_unrepaired`).
  `requirements.txt` added (`requests`, `scipy`, `pytest`) since this is the
  project's first real declared dependency (needed for `scipy.stats.wilcoxon`).
- **Fallback trigger — updated 2026-09-04**: the prior "shift to the next
  available A*-tier conference" fallback no longer applies (no external
  submission is being targeted, §1.3). If the 20-story authoring target
  clearly won't be met partway through the team timeline, the fallback is
  instead to scope down to whatever N was actually reached and report that
  honestly in the thesis — to be stated explicitly if it happens, not
  silently absorbed as if it were the original plan.
- **Still to build**: the 15 new stories themselves (hybrid-authored,
  outstanding); `scripts/generate_linear_predictions.py`; the Groq/second-
  model switch on the three existing generation scripts;
  `scripts/statistical_analysis.py` to actually run the tests above once the
  scaled dataset and predictions exist.

---

## Changelog

- **2026-08-27**: Initial version of this document. Wrote after STEP 0 (full
  read of `docs/related_work.md`, `perplexity.md`, `thesis_blueprint_v2.pdf`,
  repo file inventory, direct verification of test suite (61/61 passing) and
  saved prediction JSONs) and after resolving an ambiguity in the session's
  instructions — `Agentic cinema.md`/`Resources.md` referenced in the
  original instruction do not exist in this repo; they belong to an unrelated
  Devpost hackathon project at a different path. Confirmed with the user via
  `AskUserQuestion` that this document should cover the NonlinearTime thesis
  only; the hackathon project is out of scope and was not incorporated.
- **2026-09-03**: User instruction ("do everything you can" to assess A*-tier
  viability) authorized proceeding past the M0 checkpoint. Completed M2, M3,
  M4:
  - **M2**: targeted web-search re-verification of the two load-bearing
    novelty claims (TLEX detection-only; no prior Allen-composition-table-as-
    repair work) — both survive; found and recorded one term-colliding
    related-but-different paper (2507.03410) to cite and distinguish.
  - **M3**: first-ever real-model run of `pipeline/direct_baseline.py`
    (new `scripts/generate_direct_baseline_predictions.py`), all 5 stories.
    Found and fixed a real bug (`direct_baseline_prompt` never specified the
    required "s"-prefixed id format). Result: direct baseline beats the graph
    pipeline on relation_score for every story — **H3 as originally stated is
    falsified at pilot scale** (§5.2), with an explicit baseline-scoring
    fairness caveat recorded.
  - **M4**: first-ever real-model run of the counterfactual variant through
    the graph pipeline (new `scripts/generate_counterfactual_predictions.py`),
    all 5 stories. Found and fixed a real `KeyError: 'node_j'` crash in
    `pipeline/graph_repair.py` (switched to `.get()` + relation-vocabulary
    check). Result: headline `memorization_gap(awt_f1)` ≈0 for 4/5 stories is
    a harmonic-mean floor-effect artifact, not evidence of no gap — sub-score
    deltas reveal a real, large effect in 2/5 stories (story_04 thread
    attribution 1.000→0.044; story_05 relation 0.577→0.272), leaning toward
    **H2 positive** at pilot scale, reported with full uncertainty (§5.2).
    This also surfaces a genuine metric-design limitation of AWT-F1's
    harmonic mean for memorization-gap analysis specifically (§5.5).
  - Updated §1.4, §2, §4.1, §5.1, §5.2, §5.4, §5.5, and §6 in place to reflect
    all of the above. No content was deleted; only superseded status markers
    were updated. Per the milestone plan's own M4 checkpoint marker, the
    recommended next step is to present these findings to the user and get an
    explicit M1 venue/scope decision before any further scale-up (M5-M8) or
    paper-writing (M9).
  - **M1 decided, same day, immediately after the above was presented**:
    user chose a **full A*-scale attempt, targeting the next ARR cycle,
    falling back to the next available A*-tier conference if that timeline is
    too tight.** Verified via `aclrollingreview.org/dates` (not assumed):
    the August 2026 ARR cycle's submission deadline (Aug 3, 2026) has already
    passed as of today; the next ARR submission deadline is **October 12,
    2026** — about 5.5 weeks away. This is flagged as a hard constraint: the
    blueprint's literal 3-4k-passage/multi-model/human-baseline scope is not
    achievable solo in 5.5 weeks, so "full A*-scale attempt" is being
    interpreted as the largest scope realistically executable by that
    deadline, to be fixed in a dedicated scoping/planning pass next (M5/M6/M8
    rows marked TBD in §6 pending that pass) rather than guessed here.
- **2026-09-04**: **M1.1 — scope pivot: solo A*-conference push → 3-person
  undergraduate thesis.** User instruction, verbatim framing: this is now an
  undergraduate thesis with a 3-person team, not a solo A* push. Decided via
  `AskUserQuestion`:
  - **Timeline**: ~1 semester (~4 months) from 2026-09-04 to defense,
    replacing the prior 5.5-week ARR-cycle deadline.
  - **Team**: 3 people, all able to code (Python + web) — full
    parallelization across dataset authoring, pipeline/statistics, and web UI
    is available, replacing the prior solo-execution assumption.
  - **Dataset scale**: **N=20 retained** (unchanged from the 2026-09-03
    scoped plan, §6) — not re-scoped up or down yet, to avoid re-authoring
    stories if the pipeline methodology changes before the scale-up run.
  - **Venue**: **thesis document only** for now — external paper submission
    is explicitly not a current goal (may be revisited later if N=20 results
    are strong, but does not shape scheduling). This supersedes the
    2026-09-03 M1 decision's ARR-cycle/A*-conference target.
  - The M1 milestone row (§6) is marked superseded rather than deleted; a new
    M1.1 row records this decision. §1.3's venue framing, §6's milestone
    table/timeline note, and the M5/M6 scoped-plan bullets (Groq-model hedge,
    fallback trigger) were updated in place to remove ARR-deadline and
    solo-timeline-risk framing while keeping all still-valid content (N=20
    target, hybrid authoring method, linear-variant mechanism, statistical
    protocol) unchanged.
  - Everything already built this session and prior sessions (PCR/COC
    pipeline, AWT-F1 metric, significance tooling, linear-variant mechanism,
    5 pilot stories, the direct-baseline web UI wiring) carries over
    unchanged — this pivot re-schedules future work, it does not redo
    anything already done.
  - Also completed as part of this same session's execution: verified the
    web app's counterfactual-variant wiring builds cleanly and added a new
    "Direct baseline" view mode end-to-end (`web/src/data/index.js`,
    `web/src/components/ExamplePicker.jsx`, `web/src/App.jsx`,
    `web/src/components/Graph3D.jsx`) so a viewer can directly compare the
    graph pipeline against the direct one-shot baseline in the 3D demo and
    see the H3 finding (§5.2) surfaced as a live `relation_score` delta.
    This required adding a proper `scored_edges()` function to
    `scripts/generate_direct_baseline_predictions.py` (reusing
    `metrics/allen_relations.edge_score`, not reimplementing it) and a new
    no-LLM-call `scripts/rescore_direct_predictions.py` to backfill the 5
    already-generated `story_XX_direct.json` files. `npm run build` and
    `python -m pytest tests/ -q` (74/74) both verified clean after these
    changes; full in-browser click-through was not performed this session
    (no browser-automation tool was available) and remains an open
    verification item, stated explicitly rather than assumed done.
  - A week-by-week ~16-week thesis-plan document (research framing recap,
    finalized methodology summary, pilot findings, 3-person work-stream
    breakdown, timeline, risks, open questions) was written as a designed
    HTML page, **`thesis_plan.html` at the project root** (2026-09-05,
    moved there from a `/tmp` scratch path so it lives with the rest of the
    project and can be opened directly in a browser — no server needed).
    Publishing it as a hosted Artifact link failed in this session — the
    session authenticates via `ANTHROPIC_AUTH_TOKEN`, which the Artifact
    tool reports as incompatible with claude.ai-login-based publishing — so
    **no public link exists**; the local file is the deliverable unless
    someone runs `/login` with a claude.ai account and asks to publish it.
    Also clarified: a file named `Implementation plan.sty` opened during
    this session is an unrelated, older plan (pilot-dataset scale-up + 3D
    hub-visual restyle), not the department's thesis template — it does not
    resolve the formatting question below. Open questions flagged in the
    document itself (exact defense date, department formatting requirements
    from the as-yet-unopened `Nonlinear Temporal Reasoning.sty`,
    stream-to-name assignment) are not yet resolved in this file and should
    be filled in once known.
- **2026-09-12**: Thread-attribution leakage remediated across all 5 pilot
  stories (character names removed from the first few words of event text,
  the minimum edits needed to bring every thread under the documented
  leakage thresholds — `scripts/check_thread_leakage.py`), verified via
  `check_coverage.py` and the full test suite. story_05 was also trimmed
  (one unconnected thread dropped, 54→45 events) to fit within Groq's
  free-tier per-request token ceiling; the canonical dataset (13/13 Allen
  relation coverage) keeps story_05 at full size, only the web demo's
  manifest excludes it (user decision, confirmed via `AskUserQuestion`) —
  §5.2's table was generated before this fix and is now flagged stale in
  place rather than silently left looking current.
  - Featherless's paid subscription lapsed mid-session (billing, not a
    methodology decision) partway through re-running predictions; Groq
    (free tier, already implemented as `GroqLLMClient` but unused) was
    substituted for the remaining stories/conditions per user decision — all
    three generation scripts now take `LLM_PROVIDER=featherless|groq`. A
    Kaggle notebook (`kaggle_backup/`) was also built as a local-model
    fallback and used successfully once (story_05 direct-baseline, Qwen2.5-
    14B-Instruct 4-bit) after an initial attempt burned ~7 GPU-hours on a
    misconfigured `max_new_tokens`/retry budget — fixed and documented in
    the notebook for any future run.
  - **CRC (Convergence Recall Critique, §5.3a)**: designed via the
    brainstorming skill's architectural path (approaches proposed, literature
    researched via `agent-reach`, user approved before any code was
    written), implemented as an opt-in `pipeline/graph_pipeline.py` stage,
    tested (2 new deterministic fixture-based tests, 89/89 suite passing),
    reviewed clean by `python-reviewer`/`react-reviewer`. Live ablation
    result is honestly inconclusive at current sample size (n=4 stories, 6
    pooled gold convergence pairs) — see §5.3a for the full record,
    including a direct finding that hosted LLM inference is not run-to-run
    deterministic even at temperature 0 (discovered because CRC, which can
    only add candidates, scored *lower* than its own paired baseline on one
    story). An initial "clean win" read of the n=2 result was reported to
    the user, then corrected once the fair paired baseline and a larger
    sample were available — recorded here rather than only in conversation,
    per this document's own standard for research-integrity-relevant
    corrections.
  - **Metric reporting revised**: added `pooled_convergence_f1()` to
    `metrics/awt_f1.py` (dataset-level pooling, not a replacement for the
    existing per-story functions — see §3.3 addendum for the full
    statistical rationale) after the user directly questioned whether a
    metric that reads 0.000 on most stories was a good way to communicate
    results. The web demo's HUD hierarchy was inverted to match: relation/
    thread/convergence sub-scores are now the primary bold display, AWT-F1
    demoted to a small labeled secondary line.
  - Web demo: `web/src/data/manifest.json` trimmed to 4 stories (story_05
    excluded, per user decision above); a "With Recall Critique" comparison
    view mode added alongside the existing gold/predicted/repaired/direct
    toggles, backed by `scripts/generate_crc_predictions.py` (`USE_CRC=0`
    produces the matched same-model baseline, `USE_CRC=1` the CRC run).
  - An `awt_f1_field_guide.html` artifact was published (full AWT-F1
    formula reference, pipeline diagram, a complete real worked example on
    story_02 with every metric computed by hand against real logged
    numbers, and an explicit, undecided "does our pipeline close the gap"
    section) — not linked from this document since Artifact URLs are
    session-scoped; ask the user for the link if needed.
