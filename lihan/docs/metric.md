# AWT-F1: Allen-Weighted Temporal Graph F1

## Motivation

Plain Exact-Match, Kendall's tau, or pairwise ordering accuracy cannot score
*why* a model is wrong. Confusing `before` with `meets` is a near-miss (the
model has almost the right idea); confusing `before` with `during` is a
structural error (the model's mental model of the scene is wrong). None of
the existing metrics distinguishes these, and none of them scores thread
attribution or convergence-point detection in the same number as ordering.
"Do LLMs Understand Chronology?" (arXiv 2511.14214) shows Exact Match
collapses with sequence length even when the model's answer is nearly
correct by rank correlation — exactly the failure mode a partial-credit,
structurally-aware metric is meant to fix.

## Definition

AWT-F1 is computed per passage, given a gold temporal graph and a predicted
graph in the same shape:

```json
{
  "events": [{"id": "s1", "thread_id": "L"}, ...],
  "edges": [{"node_i": "s1", "node_j": "s2", "allen_relation": "before"}, ...],
  "convergence_points": [["s8", "s9"], ...]
}
```

**1. Relation score.** For every gold edge, score the model's predicted
relation for that node pair (in either order) using the Allen
conceptual-neighborhood distance, instead of binary correct/incorrect:

```
edge_score(gold, predicted) = max(0, 1 - distance(gold, predicted) / 6)
```

`distance` is derived directly from the definition of Allen's relations
rather than copied from Freksa's (1992) neighborhood diagram: each relation
is a total order (with ties) over the four interval endpoints
`{start1, end1, start2, end2}`, and the distance between two relations is
the number of the six pairwise endpoint comparisons on which they disagree.
This is exact, code-derivable, and unit-testable (`metrics/allen_relations.py`),
and it matches the intuition a hand-drawn neighborhood graph encodes: a
single continuous deformation of one interval past another changes exactly
one pairwise comparison, so adjacent relations in the classical neighborhood
graph are always distance 1 apart under this definition. A missing predicted
edge scores 0. The relation score for a passage is the mean over all gold
edges (vacuously 1.0 if the gold graph has no edges).

**2. Thread-attribution accuracy.** The fraction of gold events whose
predicted `thread_id` matches, by node id. A gold event with no matching
predicted node counts as incorrect.

**3. Convergence F1.** Precision/recall/F1 over unordered
same-moment node pairs. Both-empty is vacuously (1, 1, 1); a hallucinated
convergence pair against an empty gold set scores (0, 0, 0) rather than
being treated as vacuous, since a hallucinated convergence is a genuine
error.

**AWT-F1** is the harmonic mean of the three sub-scores (relation score,
thread-attribution accuracy, convergence F1); it is 0 if any sub-score is 0,
which keeps a single completely-failed dimension from being masked by strong
performance on the other two. All three sub-scores are reported alongside
the harmonic mean — this is what makes the metric diagnostic rather than a
single opaque number, and is what H3a's stage-wise failure analysis is
computed against.

**Memorization gap.** ΔAWT-F1 = AWT-F1(original) − AWT-F1(counterfactual),
computed per sub-score and overall, reusing AWT-F1 itself rather than a
second bespoke metric for RQ2/H2.

## Scope: the node-correspondence problem

CALLMSAE's Hungarian Graph Similarity (arXiv 2406.18449), the Set-Aligning
Framework's Hausdorff-distance matching (arXiv 2404.01532), and GEST's
graph-matching similarity (arXiv 2305.12940) all solve a harder problem than
AWT-F1 does: their predicted event nodes are freely-generated abstractive
text with no guaranteed 1:1 correspondence to gold nodes, so they must first
*align* predicted to gold nodes (via embedding similarity + optimal
assignment) before any edge comparison is possible.

AWT-F1 deliberately sidesteps this rather than solving it in general. Because
the pilot dataset is synthetic and every gold event is anchored to a specific
numbered input sentence, the node-extraction stage is instructed to output
the source sentence index as the node id (e.g. `s3`), giving exact
gold-predicted node correspondence by construction — a missing or
hallucinated node is simply scored as a miss, not aligned via similarity.

This is a stated, deliberate scope limitation of the pilot, not an
oversight. It is a difference from CALLMSAE/SAF/GEST, not an improvement
over them: those metrics remain necessary once event extraction is
free-text (model-generated event descriptions rather than sentence
indices), which is the natural extension needed before AWT-F1 generalizes
beyond a sentence-anchored dataset like this one.

## Implementation

`metrics/allen_relations.py` — the 13-relation endpoint-rank table,
`allen_distance`, `edge_score`; no dependencies, pure logic.

`metrics/awt_f1.py` — `relation_score`, `thread_attribution_accuracy`,
`convergence_f1`, `harmonic_mean`, `awt_f1`, `memorization_gap`.

Both are unit-tested against hand-computed cases in `tests/test_allen_relations.py`
and `tests/test_awt_f1.py` (27 tests), and exercised end-to-end against the
graph pipeline in `tests/test_pipeline.py`.
