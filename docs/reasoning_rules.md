# Temporal Reasoning Rules & Algebraic Axioms

This document details the formal rules, algebraic axioms, interval calculus, and contradiction detection logic implemented in the Temporal Reasoning Engine.

---

## 1. Allen's Interval Algebra

For two temporal intervals $X = [x_s, x_e]$ and $Y = [y_s, y_e]$ where $x_s < x_e$ and $y_s < y_e$, there are 13 mutually exclusive and exhaustive basic binary relations:

| Relation | Symbol | Inverse | Endpoint Conditions | Visual Intuition |
|---|---|---|---|---|
| **BEFORE** | $b$ | AFTER ($bi$) | $x_e < y_s$ | `[ X ] ... [ Y ]` |
| **AFTER** | $bi$ | BEFORE ($b$) | $x_s > y_e$ | `[ Y ] ... [ X ]` |
| **MEETS** | $m$ | MET_BY ($mi$) | $x_e = y_s$ | `[ X ][ Y ]` |
| **MET_BY** | $mi$ | MEETS ($m$) | $x_s = y_e$ | `[ Y ][ X ]` |
| **OVERLAPS** | $o$ | OVERLAPPED_BY ($oi$) | $x_s < y_s < x_e < y_e$ | `[ X [ Y ] X ]` |
| **OVERLAPPED_BY** | $oi$ | OVERLAPS ($o$) | $y_s < x_s < y_e < x_e$ | `[ Y [ X ] Y ]` |
| **DURING** | $d$ | CONTAINS ($di$) | $y_s < x_s < x_e < y_e$ | `... [ X ] ... in Y` |
| **CONTAINS** | $di$ | DURING ($d$) | $x_s < y_s < y_e < x_e$ | `X contains [ Y ]` |
| **STARTS** | $s$ | STARTED_BY ($si$) | $x_s = y_s \wedge x_e < y_e$ | `[ X   ]`<br>`[ Y     ]` |
| **STARTED_BY** | $si$ | STARTS ($s$) | $x_s = y_s \wedge x_e > y_e$ | `[ X     ]`<br>`[ Y   ]` |
| **FINISHES** | $f$ | FINISHED_BY ($fi$) | $x_e = y_e \wedge x_s > y_s$ | `    [ X ]`<br>`[ Y     ]` |
| **FINISHED_BY** | $fi$ | FINISHES ($f$) | $x_e = y_e \wedge x_s < y_s$ | `[ X     ]`<br>`    [ Y ]` |
| **EQUAL** | $eq$ | EQUAL ($eq$) | $x_s = y_s \wedge x_e = y_e$ | `[ X ]`<br>`[ Y ]` |

---

## 2. Inversion Axiom

Every binary relation $R$ has a well-defined inverse $R^{-1}$:

$$\forall X, Y: X \; R \; Y \iff Y \; R^{-1} \; X$$

Property:
$$(R^{-1})^{-1} = R$$

---

## 3. Composition Table (Deterministic Subsets)

Given relations $R_1$ between $A$ and $B$ ($A \; R_1 \; B$) and $R_2$ between $B$ and $C$ ($B \; R_2 \; C$), the composition $R_1 \circ R_2$ defines the relation between $A$ and $C$:

$$A \; (R_1 \circ R_2) \; C$$

### 3.1 Strict Order Compositions
- $\text{BEFORE} \circ \text{BEFORE} = \{\text{BEFORE}\}$
- $\text{BEFORE} \circ \text{MEETS} = \{\text{BEFORE}\}$
- $\text{BEFORE} \circ \text{OVERLAPS} = \{\text{BEFORE}\}$
- $\text{BEFORE} \circ \text{DURING} = \{\text{BEFORE}\}$
- $\text{BEFORE} \circ \text{STARTS} = \{\text{BEFORE}\}$
- $\text{MEETS} \circ \text{BEFORE} = \{\text{BEFORE}\}$
- $\text{MEETS} \circ \text{MEETS} = \{\text{BEFORE}\}$
- $\text{AFTER} \circ \text{AFTER} = \{\text{AFTER}\}$
- $\text{AFTER} \circ \text{MET\_BY} = \{\text{AFTER}\}$
- $\text{AFTER} \circ \text{OVERLAPPED\_BY} = \{\text{AFTER}\}$

### 3.2 Containment & Duration Compositions
- $\text{DURING} \circ \text{DURING} = \{\text{DURING}\}$
- $\text{DURING} \circ \text{BEFORE} = \{\text{BEFORE}\}$
- $\text{DURING} \circ \text{AFTER} = \{\text{AFTER}\}$
- $\text{CONTAINS} \circ \text{CONTAINS} = \{\text{CONTAINS}\}$

### 3.3 Equality Identity
For all relations $R \in \mathcal{A}$:
$$\text{EQUAL} \circ R = \{R\}$$
$$R \circ \text{EQUAL} = \{R\}$$

---

## 4. Interval Arithmetic & Boundary Completion

For any bounded event $E$:
1. $E.start\_time + E.duration = E.end\_time$
2. $E.end\_time - E.start\_time = E.duration$
3. $E.end\_time - E.duration = E.start\_time$

When two events $A$ and $B$ have resolved endpoints:
- If $A.end\_time < B.start\_time \implies A \text{ BEFORE } B$
- If $A.end\_time = B.start\_time \implies A \text{ MEETS } B$
- If $A.start\_time == B.start\_time \wedge A.end\_time == B.end\_time \implies A \text{ EQUAL } B$
- If $B.start\_time < A.start\_time \wedge A.end\_time < B.end\_time \implies A \text{ DURING } B$

---

## 5. Contradiction Detection Criteria

A temporal graph $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ is inconsistent if any of the following hold:

1. **Self-Loop Strictness Violation**:
   $$\exists v \in \mathcal{V} : (v, v) \in \mathcal{E} \text{ with relation } R \in \{\text{BEFORE}, \text{AFTER}, \text{MEETS}\}$$
2. **Disjoint Pair Collision**:
   $$\exists u, v \in \mathcal{V} : (u \xrightarrow{R_1} v) \wedge (u \xrightarrow{R_2} v) \text{ where } R_1 \cap R_2 = \emptyset$$
   *(e.g., asserting both BEFORE and AFTER between distinct $u$ and $v$)*
3. **Mutual Order Contradiction**:
   $$(u \xrightarrow{\text{BEFORE}} v) \wedge (v \xrightarrow{\text{BEFORE}} u)$$
4. **Strict Cyclic Dependency**:
   A directed cycle exists in the strict ordering subgraph $\mathcal{G}_{\text{strict}} = (\mathcal{V}, \mathcal{E}_{\text{BEFORE}} \cup \mathcal{E}_{\text{MEETS}})$.
5. **Metric Bounds Mismatch**:
   $$(u \xrightarrow{\text{BEFORE}} v) \wedge (u.start\_time \ge v.end\_time)$$
