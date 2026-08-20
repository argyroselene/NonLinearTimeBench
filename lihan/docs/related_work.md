# Related Work

This thesis extends a single direct predecessor and draws on six adjacent
literatures. The gap it fills — multi-thread narrative structure, full
Allen's-13-relation coverage, memorization-controlled counterfactual pairing,
and a diagnostic stage-wise graph pipeline, combined in one benchmark — is not
addressed by any one of them individually.

## Direct predecessor

**"Benchmarking Temporal Reasoning: Can Large Language Models Navigate Time
When Stories Refuse to Follow a Straight Line?"** (OpenReview `jogKc4OluB`,
2025) evaluates LLMs (GPT, DeepSeek, Qwen) on shuffled, single-chronology,
real-biography passages, scoring absolute/relative/mixed-time ordering. It
establishes the "shuffled numbered passage" task format this thesis reuses,
but tests only one storyline per passage and does not control for
memorization of real biographical facts. This thesis extends it along both
axes: genuinely nonlinear (multi-thread/flashback/fiction) narratives, and a
counterfactual control for memorization.

## Chronology under known facts

**"Do Large Language Models (LLMs) Understand Chronology?"** (arXiv
2511.14214) tests ordering, conditional-sort, and anachronism-detection over
memorized facts, and shows Exact Match collapses with sequence length while
rank correlation (Kendall's tau) stays comparatively high. This motivates why
Exact Match alone is an insufficient metric for this thesis's task (see
`metric.md`) — a metric is needed that survives long, high-cardinality
orderings without conflating "slightly wrong" with "completely wrong."

## Allen's interval algebra + LLMs

**QSTRBench** (arXiv 2605.18380) and **ChronoSense** (arXiv 2501.03040) test
whether LLMs can directly classify or compose Allen relations, in isolation
from any narrative context. Neither embeds full 13-relation coverage inside a
*narrative ordering* task — that embedding, as the edge-extraction stage of
this thesis's graph pipeline, is the novel link between the Allen-algebra
framing and a text-comprehension benchmark.

## Memorization-controlled counterfactual pairing

- **"The Table Says Otherwise: Testing LLMs with Counterfactual Relational
  Data"** ("ContraTable", arXiv 2606.23667) is the closest methodological
  analogue to this thesis's memorization-gap design (RQ2/H2), but perturbs
  tables, not narratives.
- **CounterBench** (arXiv 2502.11008) perturbs entity names/facts to isolate
  causal reasoning from memorized world knowledge — same logic, different
  reasoning domain (causal, not temporal).
- **Caliper** (arXiv 2606.04915) is the closest single analogue to this
  thesis's specific perturbation mechanic: it replaces meaningful variable
  names with placeholders while preserving the underlying graph structure
  exactly, isolating structural reasoning from world-knowledge recall. This
  thesis's counterfactual twins (renamed entities, shifted dates, identical
  gold graph, verified by `scripts/check_coverage.py`'s structural-signature
  diff) directly operationalize this principle for narrative text.
- **"Reasoning or Reciting?"** (NAACL 2024, arXiv 2307.02477) is the
  methodological ancestor of both ContraTable and Caliper: it establishes
  counterfactual-task perturbation as a general method for separating
  memorized-pattern recitation from generalizable reasoning.

## General temporal-reasoning benchmarks (breadth citations)

TRAM (arXiv 2310.00835) and TempReason establish the broader temporal-
reasoning benchmark landscape this thesis's task shape belongs to, without
overlapping its multi-thread/Allen-relation/counterfactual combination.

## Narrative/visual order reconstruction (adjacent domain)

MoviePuzzle (arXiv 2306.02252) and NEST (arXiv 2606.19706) establish
"reconstruct order from shuffled narrative units" as a recognized task shape
in a different modality (visual/multi-modal), not yet done text-only,
multi-thread, Allen-complete, and counterfactual-controlled.

## LLM narrative-to-graph construction pipelines

These ground the 4-stage pipeline design (§4 of the implementation plan):

- **ChronoQA / Entity-Event RAG** (ACL 2026.eacl-long.90) builds a dual
  entity/event subgraph over narrative documents.
- **STAGE** (arXiv 2601.08510) is the closest precedent for "extract a
  structured graph from a long narrative with an LLM, score it against a
  canonical gold graph" (150-screenplay benchmark, entities + typed
  relations + events).
- **Narrative Knowledge Weaver** (arXiv 2606.05724) builds narrative-centric
  RAG on episode/storyline graphs.

None of these targets multi-thread *temporal ordering* specifically or uses
Allen relations; they establish the extract-structure-evaluate pipeline
pattern this thesis specializes for temporal ordering.

## Narrative structure / flashback benchmarks

- **LitVISTA / VISTA Space** (ACL 2026.acl-long.1024) is an oracle-anchor
  literary narrative-orchestration benchmark on frontier LLMs (GPT/Claude/
  Grok/Gemini); it finds failures dominated by **anchor identification and
  localization errors**, not high-level structure reasoning. This directly
  supports this thesis's H3a prediction that failures in the graph pipeline
  will localize to the node/edge-extraction stages, not the deterministic
  sorting stages.
- **"Go Back in Time: Generating Flashbacks in Stories"** (NAACL 2022, arXiv
  2205.01898) and **TimeWeaver** (MDPI 2025) address flashback *generation*,
  not evaluation of LLM comprehension/ordering over flashback-structured
  text — useful for framing "flashback" as an established narratological
  device with prior NLP tooling (this thesis's story 2, "The Falling House,"
  follows the framing-language pattern this line of work establishes), but
  neither tests what this thesis's Set B tests.

## Event-graph similarity metrics

These confront the same core problem AWT-F1 must address — gold and
predicted nodes don't correspond 1:1 by ID — and directly inform its design
and its stated limitations (see `metric.md`):

- **CALLMSAE** (arXiv 2406.18449) proposes Hungarian Graph Similarity:
  embedding-based optimal assignment between predicted and gold event
  nodes/edges, because abstractive LLM-generated events rarely match gold
  events verbatim.
- The **Set-Aligning Framework** (arXiv 2404.01532) independently proposes
  Hausdorff-distance-based set matching for the same reason.
- **GEST** ("Graph of Events in Space and Time", arXiv 2305.12940)
  represents whole stories as event graphs with temporal/logical/spatial
  edges and defines a graph-matching similarity metric between two GESTs —
  the closest prior-art concept to AWT-F1, but general-purpose: not
  Allen-complete, no thread/convergence sub-scores, and not built for a
  memorization-controlled LLM benchmark.
- **GRAIL** (PMLR v267, 2025) uses LLM-generated code to approximate graph
  edit distance without training data.

## Novelty gap

No existing work combines (a) multi-thread narrative structure, (b) full
Allen's-13-relation coverage as the annotation schema, (c) paired
original/counterfactual memorization control, and (d) a diagnostic
stage-wise graph pipeline. This thesis's contribution is that combination,
plus the metric (AWT-F1) needed to score it.
