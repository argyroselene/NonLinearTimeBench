"""
Basic reasoning example.
Demonstrates natural language event parsing, transitivity inference,
inverse relation deduction, and contradiction detection.
"""

from temporal_reasoning import TemporalReasoningEngine, TemporalRelation


def run_basic_reasoning():
    print("=== 1. Transitive & Inverse Temporal Reasoning ===")
    engine = TemporalReasoningEngine()

    # Add statements
    engine.add_statement("Alice arrived before Bob.")
    engine.add_statement("Bob left before Charlie.")
    engine.add_statement("Charlie arrived before David.")

    # Query relations
    rel_ac = engine.query("Alice", "Charlie")
    rel_ad = engine.query("Alice", "David")
    rel_da = engine.query("David", "Alice")

    print(f"Alice vs Charlie: {rel_ac.value.upper() if rel_ac else 'UNKNOWN'}")
    print(f"Alice vs David:   {rel_ad.value.upper() if rel_ad else 'UNKNOWN'}")
    print(f"David vs Alice:   {rel_da.value.upper() if rel_da else 'UNKNOWN'}")
    print(f"Explanation (Alice -> David): {engine.query_explanation('Alice', 'David')}")
    print(f"Graph is consistent: {engine.is_consistent()}")

    print("\n=== 2. Contradiction Detection ===")
    conflict_engine = TemporalReasoningEngine()
    conflict_engine.add_statement("Meeting A happened before Meeting B.")
    conflict_engine.add_statement("Meeting B happened before Meeting A.")

    print(f"Graph is consistent: {conflict_engine.is_consistent()}")
    conflicts = conflict_engine.check_consistency()
    for c in conflicts:
        print(f"Conflict detected: [{c.conflict_type}] {c.message}")


if __name__ == "__main__":
    run_basic_reasoning()
