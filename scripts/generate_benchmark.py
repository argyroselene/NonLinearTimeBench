"""Generate benchmark and example datasets for temporal reasoning engine."""

import json
import os

examples = [
    {
        "id": "demo_01",
        "category": "event ordering",
        "statements": ["Alice arrived before Bob.", "Bob left before Charlie."],
        "query": ["Alice", "Charlie"],
        "expected": "before",
        "is_consistent": True,
    },
    {
        "id": "demo_02",
        "category": "inverse relations",
        "statements": ["Breakfast happened before Lunch."],
        "query": ["Lunch", "Breakfast"],
        "expected": "after",
        "is_consistent": True,
    },
    {
        "id": "demo_03",
        "category": "contradictions",
        "statements": ["Alpha before Beta.", "Beta before Alpha."],
        "query": ["Alpha", "Beta"],
        "expected": None,
        "is_consistent": False,
    },
]

benchmark = []

# 1. Event ordering (25 cases)
for i in range(1, 26):
    e1, e2, e3 = f"OrderA_{i}", f"OrderB_{i}", f"OrderC_{i}"
    if i % 2 == 1:
        benchmark.append({
            "id": f"eo_{i:03d}",
            "category": "event ordering",
            "statements": [f"{e1} before {e2}.", f"{e2} before {e3}."],
            "query": [e1, e3],
            "expected": "before",
            "is_consistent": True,
        })
    else:
        benchmark.append({
            "id": f"eo_{i:03d}",
            "category": "event ordering",
            "statements": [f"{e1} after {e2}.", f"{e2} after {e3}."],
            "query": [e1, e3],
            "expected": "after",
            "is_consistent": True,
        })

# 2. Transitive inference (25 cases)
for i in range(1, 26):
    e1, e2, e3, e4 = f"TransA_{i}", f"TransB_{i}", f"TransC_{i}", f"TransD_{i}"
    benchmark.append({
        "id": f"ti_{i:03d}",
        "category": "transitive inference",
        "statements": [f"{e1} before {e2}.", f"{e2} before {e3}.", f"{e3} before {e4}."],
        "query": [e1, e4],
        "expected": "before",
        "is_consistent": True,
    })

# 3. Inverse relations (20 cases)
for i in range(1, 21):
    e1, e2 = f"InvA_{i}", f"InvB_{i}"
    rel = "before" if i % 2 == 1 else "during"
    exp = "after" if rel == "before" else "contains"
    benchmark.append({
        "id": f"ir_{i:03d}",
        "category": "inverse relations",
        "statements": [f"{e1} {rel} {e2}."],
        "query": [e2, e1],
        "expected": exp,
        "is_consistent": True,
    })

# 4. Interval relations (20 cases)
interval_types = [("meets", "meets"), ("during", "during"), ("contains", "contains"), ("equal", "equal")]
for i in range(1, 21):
    e1, e2 = f"IntervalA_{i}", f"IntervalB_{i}"
    stmt_rel, exp_rel = interval_types[i % len(interval_types)]
    benchmark.append({
        "id": f"int_{i:03d}",
        "category": "interval relations",
        "statements": [f"{e1} {stmt_rel} {e2}."],
        "query": [e1, e2],
        "expected": exp_rel,
        "is_consistent": True,
    })

# 5. Relative dates (15 cases)
for i in range(1, 16):
    days = i + 1
    benchmark.append({
        "id": f"rd_{i:03d}",
        "category": "relative dates",
        "statements": [f"MeetingA_{i} happened {days} days ago.", f"MeetingB_{i} happened tomorrow."],
        "query": [f"MeetingA_{i}", f"MeetingB_{i}"],
        "expected": "before",
        "is_consistent": True,
    })

# 6. Durations (15 cases)
for i in range(1, 16):
    h = 8 + (i % 6)
    benchmark.append({
        "id": f"dur_{i:03d}",
        "category": "durations",
        "statements": [f"Lecture_{i} started at {h:02d}:00.", f"It lasted for 60 minutes.", f"Discussion_{i} started at {h+2:02d}:00."],
        "query": [f"Lecture_{i}", f"Discussion_{i}"],
        "expected": "before",
        "is_consistent": True,
    })

# 7. Contradictions (15 cases)
for i in range(1, 16):
    e1, e2, e3 = f"ConflictA_{i}", f"ConflictB_{i}", f"ConflictC_{i}"
    if i % 2 == 1:
        stmts = [f"{e1} before {e2}.", f"{e2} before {e1}."]
    else:
        stmts = [f"{e1} before {e2}.", f"{e2} before {e3}.", f"{e3} before {e1}."]
    benchmark.append({
        "id": f"contra_{i:03d}",
        "category": "contradictions",
        "statements": stmts,
        "query": [e1, e2],
        "expected": None,
        "is_consistent": False,
    })

# 8. Mixed temporal expressions (15 cases)
for i in range(1, 16):
    benchmark.append({
        "id": f"mix_{i:03d}",
        "category": "mixed temporal expressions",
        "statements": [
            f"Sprint_{i} started at 09:00.",
            f"It lasted for 2 hours.",
            f"Release_{i} started at 14:00.",
        ],
        "query": [f"Sprint_{i}", f"Release_{i}"],
        "expected": "before",
        "is_consistent": True,
    })

os.makedirs("data", exist_ok=True)
with open("data/examples.json", "w") as f:
    json.dump(examples, f, indent=2)

with open("data/benchmark.json", "w") as f:
    json.dump(benchmark, f, indent=2)

print(f"Successfully generated {len(benchmark)} benchmark examples and {len(examples)} demo examples.")
