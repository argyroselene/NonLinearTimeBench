# Temporal Reasoning Engine — Architecture Documentation

This document describes the design, module responsibilities, data flow, and representations employed in the Temporal Reasoning Engine.

---

## 1. System Overview

The engine translates natural-language statements containing temporal events, dates, durations, and relations into an explicit, symbolic graph representation. Once instantiated, the graph is closed under deterministic algebraic inference rules to infer implicit temporal relationships and detect contradictions.

```
+─────────────────────────────────────────────────────────────+
|                    Natural Language Input                   |
+─────────────────────────────────────────────────────────────+
                              │
                              ▼
+─────────────────────────────────────────────────────────────+
|          Temporal Expression Extractor (expressions.py)     |
|   - Regex & rule pattern recognition                        |
|   - Dates, Clock Times, Durations, Relative Offsets         |
+─────────────────────────────────────────────────────────────+
                              │
                              ▼
+─────────────────────────────────────────────────────────────+
|              Temporal Normalizer (normalizer.py)            |
|   - Unit conversion, anchor-date resolution                 |
|   - ISO datetime & timedelta construction                   |
+─────────────────────────────────────────────────────────────+
                              │
                              ▼
+─────────────────────────────────────────────────────────────+
|               Statement Parser (parser.py)                  |
|   - Entity extraction & pronoun/coreference resolution      |
|   - Statement classification: Relation vs Event Bound       |
+─────────────────────────────────────────────────────────────+
                              │
                              ▼
+─────────────────────────────────────────────────────────────+
|                 Temporal Graph (graph.py)                   |
|   - Nodes: Event objects                                    |
|   - Directed Edges: TemporalRelation labels + provenance    |
+─────────────────────────────────────────────────────────────+
                              │
                              ▼
+─────────────────────────────────────────────────────────────+
|             Deterministic Inference (inference.py)          |
|   - Algebraic Inversion (A R B <=> B inv(R) A)             |
|   - Path Transitivity (A R1 B ^ B R2 C => A R3 C)          |
|   - Point & Interval Bound Arithmetic (start+dur=end)       |
|   - Direct Allen Interval Deduction                         |
+─────────────────────────────────────────────────────────────+
                              │
                              ▼
+─────────────────────────────────────────────────────────────+
|             Consistency Checker (consistency.py)            |
|   - Disjoint relation conflict detection                    |
|   - Directed cycle detection on strict orders (DFS)         |
|   - Timestamp vs graph relation mismatch verification       |
+─────────────────────────────────────────────────────────────+
                              │
                              ▼
+─────────────────────────────────────────────────────────────+
|              Query Interface & CLI (engine.py, cli.py)      |
|   - Relation lookups, provenance explanations, DOT export   |
+─────────────────────────────────────────────────────────────+
```

---

## 2. Core Modules

### 2.1 Event Data Model (`events.py`)
Encapsulates an event entity with unique identifier, descriptive label, and optional temporal boundaries:
- `event_id`: Unique identifier (e.g. `E1`, `Meeting_1`).
- `description`: Textual event description.
- `start_time`: `datetime` object indicating event start.
- `end_time`: `datetime` object indicating event finish.
- `duration`: `timedelta` indicating duration.
- Validation invariants guarantee: $start\_time \le end\_time$ and $duration = end\_time - start\_time$ when both are present.

### 2.2 Temporal Relation Vocabulary (`relations.py`)
Implements the 13 foundational relations from Allen's Interval Algebra:
- `BEFORE`, `AFTER`
- `EQUAL`
- `MEETS`, `MET_BY`
- `OVERLAPS`, `OVERLAPPED_BY`
- `DURING`, `CONTAINS`
- `STARTS`, `STARTED_BY`
- `FINISHES`, `FINISHED_BY`

Each relation possesses an exact inverse mapping and participates in a deterministic composition lookup table.

### 2.3 Expression Extraction (`expressions.py`)
Regex and token scanning module that extracts temporal clauses:
- Named relative days (`today`, `yesterday`, `tomorrow`).
- Offset relative dates (`2 days ago`, `3 weeks later`).
- Day-of-week mentions (`last Monday`, `next Friday`).
- Clock times (`10:30`, `2:15 pm`, `14:00`).
- Absolute calendar dates (`12 March 2026`, `2026-09-10`).
- Durations (`for 90 minutes`, `for two hours`).

### 2.4 Normalization Engine (`normalizer.py`)
Maps extracted surface forms into normalized, machine-readable structures:
- Calculates relative offsets against reference anchor dates (default: `2026-09-13`).
- Resolves weekday modulo calculations to identify target dates.
- Standardizes duration representations into seconds and `timedelta` instances.

### 2.5 Statement Parser (`parser.py`)
Processes raw sentences to extract event entities and identify relation structures:
- Multi-sentence parsing and coreference tracking: maintains `last_event` state so follow-up sentences like *"It lasted for 90 minutes."* bind duration directly to the antecedent event.
- Cleans and canonicalizes entity names by stripping auxiliary action verbs.

### 2.6 Graph Data Structure (`graph.py`)
A directed multigraph representing events and relations:
- Stores explicit and inferred edges distinctly.
- Retains confidence scores and provenance annotations for every edge.
- Provides BFS path-finding and Graphviz DOT serialization for visual diagnostics.

### 2.7 Inference Engine (`inference.py`)
Iteratively computes the relational closure of the temporal graph:
1. **Inverse Propagation**: For each $(u \xrightarrow{R} v)$, asserts $(v \xrightarrow{R^{-1}} u)$.
2. **Transitivity / Path Consistency**: For each $(u \xrightarrow{R_1} v)$ and $(v \xrightarrow{R_2} w)$, consults the algebraic composition table. If a deterministic single relation $R_3$ results, asserts $(u \xrightarrow{R_3} w)$ with provenance tracking.
3. **Bound Completion**: Derives missing bounds via $start + duration = end$, $end - start = duration$, and $end - duration = start$.
4. **Allen Interval Deduction**: When boundaries for both intervals are resolved, evaluates point comparisons to establish the exact Allen relation.

### 2.8 Consistency Checker (`consistency.py`)
Validates logical integrity through multiple checks:
- Self-loop detection for strict orderings (e.g. $A < A$).
- Disjoint relation contradictions between identical pairs (e.g. asserting both `BEFORE` and `AFTER`).
- Mutual ordering contradictions ($A \text{ BEFORE } B$ and $B \text{ BEFORE } A$).
- Topological cycle detection on strict ordering relations using Depth-First Search.
- Grounded timestamp vs asserted edge compatibility.

### 2.9 Unified Query Engine (`engine.py`)
Coordinates parsing, auto-inference, and queries into a single Python class:
- `engine.add_statement(...)`
- `engine.query(event_a, event_b) -> TemporalRelation`
- `engine.query_explanation(event_a, event_b) -> str`
- `engine.check_consistency() -> List[TemporalConflict]`
