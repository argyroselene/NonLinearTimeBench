# Temporal Reasoning Project — Agent Build Guideline

## 1. Objective

Build a small but credible open-source project demonstrating **temporal reasoning over natural-language events**.

The repository should look like a genuine research/engineering project rather than a collection of toy scripts. It should include:

- Temporal expression normalization
- Event extraction
- Temporal relations
- Rule-based temporal inference
- Interval reasoning
- A small benchmark/dataset
- Evaluation metrics
- Unit tests
- Documentation
- Reproducible experiments

### Important contribution-history rule

The commit schedule below is a **development plan**, not a request to fabricate GitHub history.

Only create a dated commit after the corresponding work has actually been completed. Do **not** backdate commits or claim work happened on a date when it did not. If development happens on different dates, use the actual dates.

---

# 2. Suggested Repository

Repository name:

```text
temporal-reasoning-engine
```

Suggested description:

> A lightweight symbolic temporal reasoning engine for extracting, normalizing, and inferring temporal relations between events.

Suggested topics:

```text
temporal-reasoning
nlp
natural-language-processing
event-ordering
temporal-relations
symbolic-reasoning
python
```

---

# 3. Core Research/Engineering Question

Given a collection of natural-language statements describing events, can we convert them into normalized temporal representations and infer relations that were not explicitly stated?

Example:

```text
Alice arrived before Bob.
Bob left before Charlie.
```

The system should infer:

```text
Alice BEFORE Bob
Bob BEFORE Charlie
Alice BEFORE Charlie
```

Another example:

```text
The meeting started at 10:00.
It lasted for 90 minutes.
```

The system should infer:

```text
START = 10:00
END = 11:30
DURATION = 90 minutes
```

---

# 4. Architecture

Use a modular Python implementation.

```text
Input Text
    │
    ▼
Temporal Expression Extraction
    │
    ▼
Temporal Normalization
    │
    ▼
Event Extraction
    │
    ▼
Temporal Relation Extraction
    │
    ▼
Temporal Graph Construction
    │
    ▼
Rule-Based Temporal Inference
    │
    ▼
Consistency Checking
    │
    ▼
Query / Evaluation
```

Recommended modules:

```text
src/temporal_reasoning/
├── __init__.py
├── events.py
├── expressions.py
├── relations.py
├── normalizer.py
├── graph.py
├── inference.py
├── consistency.py
├── parser.py
└── evaluator.py
```

---

# 5. Repository Structure

Create approximately:

```text
temporal-reasoning-engine/
│
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── src/
│   └── temporal_reasoning/
│       ├── __init__.py
│       ├── events.py
│       ├── expressions.py
│       ├── relations.py
│       ├── normalizer.py
│       ├── parser.py
│       ├── graph.py
│       ├── inference.py
│       ├── consistency.py
│       └── evaluator.py
│
├── data/
│   ├── examples.json
│   └── benchmark.json
│
├── tests/
│   ├── test_expressions.py
│   ├── test_relations.py
│   ├── test_inference.py
│   └── test_consistency.py
│
├── examples/
│   ├── basic_reasoning.py
│   └── interval_reasoning.py
│
├── notebooks/
│   └── evaluation.ipynb
│
└── docs/
    ├── architecture.md
    └── reasoning_rules.md
```

---

# 6. Temporal Relation Vocabulary

Start with a manageable relation set:

```text
BEFORE
AFTER
EQUAL
MEETS
OVERLAPS
DURING
STARTS
FINISHES
CONTAINS
```

Represent relations using an enum.

Example:

```python
class TemporalRelation(Enum):
    BEFORE = "before"
    AFTER = "after"
    EQUAL = "equal"
    MEETS = "meets"
    OVERLAPS = "overlaps"
    DURING = "during"
    STARTS = "starts"
    FINISHES = "finishes"
    CONTAINS = "contains"
```

Implement inverse relations where appropriate.

For example:

```text
BEFORE ↔ AFTER
DURING ↔ CONTAINS
STARTS ↔ STARTED-BY
FINISHES ↔ FINISHED-BY
```

---

# 7. Temporal Expressions

Support expressions such as:

```text
today
yesterday
tomorrow
last Monday
next Friday
two days ago
three weeks later
at 10:30
on 12 March 2026
for two hours
before the meeting
after lunch
```

Normalize expressions into structured representations.

Example:

```json
{
  "text": "two days later",
  "type": "RELATIVE_DATE",
  "value": 2,
  "unit": "day",
  "direction": "future"
}
```

Use Python's standard datetime functionality where possible.

---

# 8. Event Representation

Create an Event object containing at least:

```text
event_id
description
start_time
end_time
duration
```

Example:

```json
{
  "event_id": "E1",
  "description": "Alice arrived",
  "start_time": "2026-09-10T09:00:00",
  "end_time": null,
  "duration": null
}
```

---

# 9. Temporal Graph

Represent events as nodes and temporal relations as directed edges.

Example:

```text
Alice arrived
      │
      │ BEFORE
      ▼
Bob arrived
      │
      │ BEFORE
      ▼
Charlie arrived
```

The graph should support:

- Adding events
- Adding relations
- Querying relations
- Finding paths
- Detecting contradictions
- Exporting the graph

---

# 10. Inference Rules

Implement deterministic inference rules.

### Transitivity

```text
A BEFORE B
B BEFORE C
────────────
A BEFORE C
```

### Inverse relation

```text
A BEFORE B
──────────
B AFTER A
```

### Equality

```text
A EQUAL B
B BEFORE C
────────────
A BEFORE C
```

### Contradiction

Detect:

```text
A BEFORE B
B BEFORE A
```

when the events are not equal.

### Interval reasoning

If:

```text
A STARTS at 10:00
A DURATION = 2 hours
```

infer:

```text
A ENDS at 12:00
```

Keep the inference engine deterministic and explainable.

---

# 11. Query Interface

Provide a simple Python API:

```python
engine = TemporalReasoningEngine()

engine.add_statement(
    "Alice arrived before Bob."
)

engine.add_statement(
    "Bob left before Charlie."
)

result = engine.query(
    "Alice", "Charlie"
)
```

Expected result:

```text
BEFORE
```

Also provide a CLI:

```bash
python -m temporal_reasoning.cli \
    --input examples/basic.txt \
    --query "Alice" "Charlie"
```

---

# 12. Benchmark

Create a small manually verified benchmark.

Target:

```text
100–300 examples
```

Categories:

```text
event ordering
relative dates
durations
interval relations
transitive inference
inverse relations
contradictions
mixed temporal expressions
```

Each example should contain:

```json
{
  "id": "ex_001",
  "statements": [
    "A happened before B.",
    "B happened before C."
  ],
  "query": ["A", "C"],
  "answer": "BEFORE"
}
```

Do not copy copyrighted datasets wholesale. Small manually authored examples are sufficient for this project.

---

# 13. Evaluation

Implement at least:

```text
Accuracy
Precision
Recall
F1
Consistency rate
Inference accuracy
```

Separate:

```text
explicit relation accuracy
```

from:

```text
inferred relation accuracy
```

Generate a simple evaluation report.

Example:

```text
Temporal Reasoning Evaluation
-----------------------------
Examples:              200
Explicit Accuracy:     96.5%
Inference Accuracy:    91.0%
Consistency Rate:      98.0%
Macro F1:              0.93
```

Do not invent these numbers. Generate them from actual experiments.

---

# 14. Tests

Use `pytest`.

Test:

- Date normalization
- Relative dates
- Event construction
- Relation inversion
- Transitivity
- Interval arithmetic
- Contradiction detection
- Query results
- Malformed input
- Empty input

Target at least:

```text
25–40 meaningful tests
```

---

# 15. Documentation

README should contain:

1. Project motivation
2. Features
3. Architecture
4. Installation
5. Quick-start example
6. Supported temporal relations
7. Inference rules
8. Benchmark
9. Evaluation
10. Limitations
11. Future work
12. License

Avoid claiming that this is a state-of-the-art system.

Describe it accurately as a lightweight, interpretable temporal reasoning engine.

---

# 16. Development Commit Plan

The following is a **20-stage development plan**. These dates are suggested milestones for a one-month development cycle. They must be changed to the actual dates on which the work is performed if the implementation does not follow this schedule.

### Stage 01 — Project initialization
Planned date: 2026-09-01

Create:

```text
README.md
.gitignore
LICENSE
pyproject.toml
requirements.txt
src/
tests/
```

Commit message:

```text
Initialize temporal reasoning project
```

---

### Stage 02 — Event data model
Planned date: 2026-09-03

Implement the Event representation and basic serialization.

Commit:

```text
Add temporal event data model
```

---

### Stage 03 — Temporal relation model
Planned date: 2026-09-04

Implement relation enums and inverse mappings.

Commit:

```text
Add temporal relation vocabulary
```

---

### Stage 04 — Temporal expression extraction
Planned date: 2026-09-06

Implement extraction of basic expressions:

```text
today
yesterday
tomorrow
dates
times
durations
```

Commit:

```text
Implement temporal expression extraction
```

---

### Stage 05 — Temporal normalization
Planned date: 2026-09-08

Convert extracted expressions into normalized structures.

Commit:

```text
Add temporal expression normalization
```

---

### Stage 06 — Natural-language statement parser
Planned date: 2026-09-10

Parse simple statements into events and relations.

Commit:

```text
Implement temporal statement parser
```

---

### Stage 07 — Temporal graph
Planned date: 2026-09-12

Implement graph construction and relation queries.

Commit:

```text
Add temporal relation graph
```

---

### Stage 08 — Relation inversion
Planned date: 2026-09-14

Implement inverse relation inference.

Commit:

```text
Add inverse temporal relation inference
```

---

### Stage 09 — Transitive reasoning
Planned date: 2026-09-16

Implement transitive reasoning for supported relations.

Commit:

```text
Implement temporal transitivity
```

---

### Stage 10 — Interval reasoning
Planned date: 2026-09-18

Add start/end/duration reasoning.

Commit:

```text
Add temporal interval reasoning
```

---

### Stage 11 — Consistency checking
Planned date: 2026-09-20

Detect temporal contradictions and invalid graphs.

Commit:

```text
Add temporal consistency checker
```

---

### Stage 12 — Query engine
Planned date: 2026-09-21

Implement natural-language and programmatic relation queries.

Commit:

```text
Add temporal reasoning query engine
```

---

### Stage 13 — Benchmark dataset
Planned date: 2026-09-23

Add the manually verified benchmark examples.

Commit:

```text
Add temporal reasoning benchmark
```

---

### Stage 14 — Evaluation framework
Planned date: 2026-09-24

Implement accuracy, precision, recall, F1, and consistency metrics.

Commit:

```text
Add temporal reasoning evaluation
```

---

### Stage 15 — Unit tests
Planned date: 2026-09-25

Expand test coverage across parsing, normalization, inference, and consistency.

Commit:

```text
Expand temporal reasoning test coverage
```

---

### Stage 16 — CLI
Planned date: 2026-09-26

Add a command-line interface.

Commit:

```text
Add temporal reasoning CLI
```

---

### Stage 17 — Examples
Planned date: 2026-09-27

Add practical examples demonstrating:

```text
event ordering
date reasoning
duration reasoning
contradiction detection
```

Commit:

```text
Add temporal reasoning examples
```

---

### Stage 18 — Evaluation experiment
Planned date: 2026-09-28

Run the benchmark and save actual results.

Commit:

```text
Add benchmark evaluation results
```

Only include numbers that were actually produced by the experiment.

---

### Stage 19 — Documentation and architecture
Planned date: 2026-09-29

Improve README and add architecture/reasoning documentation.

Commit:

```text
Document temporal reasoning architecture
```

---

### Stage 20 — Release cleanup
Planned date: 2026-09-30

Clean APIs, remove dead code, fix tests, verify installation, and prepare the repository for public use.

Commit:

```text
Prepare initial temporal reasoning release
```

---

# 17. Git Workflow

For every completed milestone:

```bash
git status
git add .
git diff --cached
git commit -m "<message>"
git push origin main
```

Before each commit:

1. Run tests.
2. Verify that the changed functionality actually works.
3. Update documentation where appropriate.
4. Do not commit generated junk, credentials, local environments, or large model files.

Use:

```bash
pytest
```

before pushing.

---

# 18. Agent Instructions

The coding agent should:

- Work incrementally.
- Keep commits focused.
- Run tests after meaningful changes.
- Never fabricate evaluation results.
- Never fabricate authorship or development activity.
- Never backdate commits merely to manipulate the GitHub contribution graph.
- Use the actual completion date for each commit.
- Push only after the corresponding work exists in the repository.
- Keep the project runnable after every major milestone.
- Prefer simple, deterministic implementations over unnecessary complexity.
- Update the README as functionality grows.
- Do not claim external datasets, papers, benchmarks, or results were used unless they were actually used.

---

# 19. Final Quality Checklist

Before considering the project complete:

```text
[ ] Repository has a clear README
[ ] Installation works from a clean environment
[ ] Core temporal relations are implemented
[ ] Temporal expressions are normalized
[ ] Events can be represented
[ ] Temporal graph works
[ ] Inference rules work
[ ] Contradictions are detected
[ ] Query API works
[ ] CLI works
[ ] Benchmark exists
[ ] Evaluation is reproducible
[ ] Tests pass
[ ] Examples work
[ ] No fabricated results
[ ] No secrets committed
[ ] Git history reflects actual development
```

# 20. Optional Extensions

If the core project is stable, consider:

```text
- Allen's interval algebra
- probabilistic temporal relations
- visualization of temporal graphs
- support for recurring events
- timezone-aware reasoning
- integration with a small LLM parser
- natural-language query generation
- benchmark comparison between symbolic and LLM reasoning
```

These should be added only after the core deterministic engine is reliable.
