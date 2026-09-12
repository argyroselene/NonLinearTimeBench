# Temporal Reasoning Engine

A lightweight, interpretable, symbolic temporal reasoning engine in Python for extracting, normalizing, and inferring temporal relations between natural-language events.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

---

## 1. Project Motivation

Natural language descriptions of processes, narratives, and historical records routinely rely on implicit temporal structures:
- Events ordered sequentially (*"Alice arrived before Bob. Bob left before Charlie."*)
- Events defined with relative dates and calendar expressions (*"Two days ago", "next Friday"*)
- Temporal intervals bounded by durations (*"The seminar started at 10:00 and lasted for 90 minutes."*)

While modern large language models can perform temporal answering, their reasoning frequently suffers from hallucinated orderings, path inconsistency, and an absence of verifiable mathematical provenance.

The **Temporal Reasoning Engine** provides a lightweight, deterministic, symbolic alternative. It parses text into standardized event entities, normalizes temporal expressions, constructs a directed temporal graph, and computes deductive closures using Allen's Interval Algebra and interval arithmetic while strictly detecting contradictions.

---

## 2. Key Features

- **Temporal Expression Extraction & Normalization**: Regex- and rule-based extraction supporting relative dates (*"today"*, *"two days ago"*), clock times (*"10:30"*, *"2:15 pm"*), absolute dates (*"12 March 2026"*), and durations (*"for 90 minutes"*).
- **Allen's Interval Algebra**: Full 13-relation interval vocabulary (`BEFORE`, `AFTER`, `EQUAL`, `MEETS`, `MET_BY`, `OVERLAPS`, `OVERLAPPED_BY`, `DURING`, `CONTAINS`, `STARTS`, `STARTED_BY`, `FINISHES`, `FINISHED_BY`).
- **Deterministic Inference Engine**:
  - Exact inverse mapping ($A \text{ BEFORE } B \iff B \text{ AFTER } A$).
  - Path consistency & transitivity ($A \text{ BEFORE } B \wedge B \text{ BEFORE } C \implies A \text{ BEFORE } C$).
  - Boundary arithmetic ($start + duration = end$).
  - Automatic Allen interval deduction from metric timestamps.
- **Explainable Provenance**: Every inferred edge records the exact derivation rule and antecedent paths.
- **Strict Contradiction Detection**: Detects disjoint relations, mutual inversions, metric timestamp conflicts, and topological cycles.
- **Command-Line Interface (CLI)**: Interactive REPL, batch file processor, and benchmark runner.
- **Reproducible Evaluation**: 150-example manually verified benchmark spanning 8 temporal categories with reproducible metrics.

---

## 3. Architecture

```
Natural Language Text
        │
        ▼
Temporal Expression Extraction (expressions.py)
        │
        ▼
Temporal Normalization (normalizer.py)
        │
        ▼
Event & Statement Parsing (parser.py)
        │
        ▼
Temporal Graph Construction (graph.py)
        │
        ▼
Deterministic Inference Closure (inference.py)
        │
        ▼
Consistency & Contradiction Checking (consistency.py)
        │
        ▼
Query Interface & Evaluation (engine.py, evaluator.py, cli.py)
```

For detailed specifications, see [Architecture Documentation](docs/architecture.md) and [Reasoning Rules](docs/reasoning_rules.md).

---

## 4. Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/argyroselene/NonLinearTimeBench.git
cd NonLinearTimeBench
pip install -e .
```

To install test dependencies:

```bash
pip install -r requirements.txt
```

---

## 5. Quick-Start Example

### Python API

```python
from temporal_reasoning import TemporalReasoningEngine, TemporalRelation

# Initialize engine
engine = TemporalReasoningEngine()

# Add statements
engine.add_statement("Alice arrived before Bob.")
engine.add_statement("Bob left before Charlie.")

# Query relation between Alice and Charlie
relation = engine.query("Alice", "Charlie")
print("Relation:", relation.value.upper())
# Output: Relation: BEFORE

# Query explanation
print("Provenance:", engine.query_explanation("Alice", "Charlie"))
# Output: Provenance: Transitivity: (E1 before E2) and (E2 before E3)

# Check graph consistency
print("Consistent:", engine.is_consistent())
# Output: Consistent: True
```

### Interval Reasoning Example

```python
from datetime import datetime
from temporal_reasoning import TemporalReasoningEngine

engine = TemporalReasoningEngine(anchor_date=datetime(2026, 9, 13))

# Define start and duration
engine.add_statement("The meeting started at 10:00. It lasted for 90 minutes.")
engine.add_statement("The presentation started at 12:00.")

# Automatically infers:
# 1. Meeting end_time = 11:30
# 2. Meeting BEFORE Presentation
print("Relation:", engine.query("The meeting", "The presentation"))
# Output: Relation: BEFORE
```

### Command-Line Interface (CLI)

Query relations from text statements directly:

```bash
python -m temporal_reasoning.cli \
    -s "Alice arrived before Bob." \
    -s "Bob left before Charlie." \
    -q "Alice" "Charlie"
```

Start interactive REPL mode:

```bash
python -m temporal_reasoning.cli --interactive
```

---

## 6. Supported Temporal Relations

| Relation | Enum Member | Inverse | Description |
|---|---|---|---|
| Before | `BEFORE` | `AFTER` | Event A finishes before B starts |
| After | `AFTER` | `BEFORE` | Event A starts after B finishes |
| Equal | `EQUAL` | `EQUAL` | Event A and B share identical start and end |
| Meets | `MEETS` | `MET_BY` | Event A finishes at the instant B starts |
| Met By | `MET_BY` | `MEETS` | Event A starts at the instant B finishes |
| Overlaps | `OVERLAPS` | `OVERLAPPED_BY` | Event A starts before B, ends during B |
| Overlapped By | `OVERLAPPED_BY` | `OVERLAPS` | Event B starts before A, ends during A |
| During | `DURING` | `CONTAINS` | Event A occurs entirely within B |
| Contains | `CONTAINS` | `DURING` | Event A spans beyond start and end of B |
| Starts | `STARTS` | `STARTED_BY` | Event A and B share start, A finishes earlier |
| Started By | `STARTED_BY` | `STARTS` | Event A and B share start, A finishes later |
| Finishes | `FINISHES` | `FINISHED_BY` | Event A and B share end, A starts later |
| Finished By | `FINISHED_BY` | `FINISHES` | Event A and B share end, A starts earlier |

---

## 7. Inference Rules

1. **Transitivity**:
   $$\forall A, B, C: (A \text{ BEFORE } B) \wedge (B \text{ BEFORE } C) \implies A \text{ BEFORE } C$$
2. **Inversion**:
   $$\forall A, B: (A \; R \; B) \iff (B \; R^{-1} \; A)$$
3. **Equality Substitution**:
   $$\forall A, B, C: (A \text{ EQUAL } B) \wedge (B \; R \; C) \implies A \; R \; C$$
4. **Interval Arithmetic**:
   $$start\_time + duration = end\_time$$
5. **Metric-to-Interval Deduction**:
   When concrete endpoints are known, Allen relations are deduced via exact boundary comparisons.

---

## 8. Benchmark Dataset

The repository includes a manually curated and verified benchmark of **150 examples** across 8 core categories:

| Category | Examples | Focus |
|---|---|---|
| `event ordering` | 25 | Sequential multi-hop ordering chains |
| `transitive inference` | 25 | 3- and 4-event transitive reasoning |
| `inverse relations` | 20 | Bidirectional reciprocal queries |
| `interval relations` | 20 | Meets, during, contains, and equal relations |
| `relative dates` | 15 | Offsets (days ago, weeks later, tomorrow) |
| `durations` | 15 | Interval completion ($start + dur \to end$) |
| `contradictions` | 15 | Direct and cyclic contradictions |
| `mixed temporal expressions` | 15 | Clock times combined with durations and dates |

Dataset location: [`data/benchmark.json`](data/benchmark.json)

---

## 9. Evaluation Results

Results generated by running the automated benchmark suite:

```bash
python scripts/run_benchmark.py
```

### Empirical Performance Summary

```text
==================================================
          Temporal Reasoning Evaluation           
==================================================
Total Examples:          150
Overall Accuracy:        100.0%
Explicit Accuracy:       100.0%
Inference Accuracy:      100.0%
Consistency Rate:        100.0%
Macro Precision:         1.000
Macro Recall:            1.000
Macro F1 Score:          1.000
--------------------------------------------------
Category Breakdown:
  - contradictions            : 15/15 (100.0%)
  - durations                 : 15/15 (100.0%)
  - event ordering            : 25/25 (100.0%)
  - interval relations        : 20/20 (100.0%)
  - inverse relations         : 20/20 (100.0%)
  - mixed temporal expressions: 15/15 (100.0%)
  - relative dates            : 15/15 (100.0%)
  - transitive inference      : 25/25 (100.0%)
==================================================
```

*All numbers represent actual experimental outputs stored in [`data/benchmark_results.json`](data/benchmark_results.json).*

---

## 10. Limitations

- **Syntactic Simplicity**: The statement parser uses deterministic rules and regular expressions tailored for structured declarative sentences. Complex narrative prose with nested relative clauses may require preliminary entity and dependency extraction.
- **Disjunctive Ambiguity**: The current composition closure focuses on deterministic single-relation outcomes; relations yielding large disjunctive sets (e.g., $A \text{ OVERLAPS } B \wedge B \text{ OVERLAPS } C$) are stored as unconstrained rather than full disjunctive constraint networks.
- **Reference Anchoring**: Relative dates assume an anchor date context; unanchored relative statements require an explicit reference point.

---

## 11. Future Work

- **Disjunctive Allen Algebra (Path Consistency / Allen's Full Network Algorithm)**.
- **Probabilistic / Fuzzy Temporal Reasoning** for uncertain or approximate boundaries (*"roughly two hours"*).
- **Timezone and Calendar Logic** integrating comprehensive locale-aware daylight savings rules.
- **Hybrid Neural-Symbolic Pipeline**: Coupling an LLM semantic extractor with this symbolic inference engine for verifiable natural language reasoning.

---

## 12. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
