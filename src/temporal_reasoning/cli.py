"""
Command-Line Interface (CLI) for Temporal Reasoning Engine.
Supports batch statements, relation queries, benchmark evaluation,
consistency checking, and graph exporting.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from typing import List, Optional

from temporal_reasoning import (
    TemporalReasoningEngine,
    BenchmarkEvaluator,
    TemporalRelation,
    __version__,
)


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="temporal-reasoning",
        description="Lightweight symbolic temporal reasoning engine CLI.",
    )
    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Path to a text file containing natural-language temporal statements.",
    )
    parser.add_argument(
        "--statement", "-s",
        type=str,
        action="append",
        help="Direct statement to add (can be specified multiple times).",
    )
    parser.add_argument(
        "--query", "-q",
        nargs=2,
        metavar=("EVENT_A", "EVENT_B"),
        help="Query the temporal relation between two events.",
    )
    parser.add_argument(
        "--check-consistency", "-c",
        action="store_true",
        help="Check the temporal graph for contradictions.",
    )
    parser.add_argument(
        "--evaluate", "-e",
        type=str,
        metavar="BENCHMARK_JSON",
        help="Run evaluation against a benchmark JSON dataset.",
    )
    parser.add_argument(
        "--export-dot",
        type=str,
        metavar="OUTPUT_DOT",
        help="Export graph visualization in Graphviz DOT format.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start an interactive temporal reasoning shell.",
    )
    return parser


def run_interactive(engine: TemporalReasoningEngine):
    """Run an interactive REPL shell."""
    print("==================================================")
    print("    Temporal Reasoning Engine Interactive Shell   ")
    print(" Type statements to add, or 'query <A> <B>'       ")
    print(" Type 'graph' to inspect, 'exit' to quit.        ")
    print("==================================================")

    while True:
        try:
            line = input("temporal> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break
        if line.lower() == "reset":
            engine.reset()
            print("Engine reset.")
            continue
        if line.lower() == "graph":
            print(f"Events: {len(engine.graph.events)}")
            for edge in engine.graph.get_all_edges():
                status = "[inferred]" if edge.is_inferred else "[explicit]"
                print(f"  {edge.source_id} --({edge.relation.value})--> {edge.target_id} {status}")
            continue

        if line.lower().startswith("query "):
            parts = line.split()[1:]
            if len(parts) == 2:
                rel = engine.query(parts[0], parts[1])
                print(f"Result: {rel.value if rel else 'NO RELATION FOUND'}")
            else:
                print("Usage: query <event_a> <event_b>")
            continue

        # Otherwise treat as statement
        parsed = engine.add_statement(line)
        print(f"Parsed {len(parsed)} statement(s). Graph consistent: {engine.is_consistent()}")


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    engine = TemporalReasoningEngine()

    # Benchmark evaluation mode
    if parsed_args.evaluate:
        path = Path(parsed_args.evaluate)
        if not path.exists():
            print(f"Error: Benchmark file '{path}' not found.", file=sys.stderr)
            return 1
        evaluator = BenchmarkEvaluator()
        metrics = evaluator.evaluate_file(path)
        print(metrics.summary_report())
        return 0

    # Load statements from input file
    if parsed_args.input:
        in_path = Path(parsed_args.input)
        if not in_path.exists():
            print(f"Error: Input file '{in_path}' not found.", file=sys.stderr)
            return 1
        with open(in_path, "r", encoding="utf-8") as f:
            content = f.read()
        engine.add_statement(content)

    # Load statements from CLI flags
    if parsed_args.statement:
        for stmt in parsed_args.statement:
            engine.add_statement(stmt)

    # Interactive mode
    if parsed_args.interactive:
        run_interactive(engine)
        return 0

    # Consistency check
    if parsed_args.check_consistency:
        conflicts = engine.check_consistency()
        if conflicts:
            print(f"Found {len(conflicts)} temporal conflict(s):")
            for c in conflicts:
                print(f"  - [{c.conflict_type}]: {c.message}")
        else:
            print("Temporal graph is logically consistent.")

    # Query execution
    if parsed_args.query:
        src, tgt = parsed_args.query
        relation = engine.query(src, tgt)
        if relation:
            print(f"Relation ({src} -> {tgt}): {relation.value.upper()}")
            explanation = engine.query_explanation(src, tgt)
            if explanation:
                print(f"Provenance: {explanation}")
        else:
            print(f"No deterministic relation found between '{src}' and '{tgt}'.")

    # Export DOT
    if parsed_args.export_dot:
        dot_str = engine.graph.to_dot()
        with open(parsed_args.export_dot, "w", encoding="utf-8") as f:
            f.write(dot_str)
        print(f"Graph exported to '{parsed_args.export_dot}'.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
