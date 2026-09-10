"""Run benchmark evaluation and store empirical results."""

import json
from pathlib import Path
from temporal_reasoning.evaluator import BenchmarkEvaluator


def main():
    benchmark_file = Path("data/benchmark.json")
    if not benchmark_file.exists():
        raise FileNotFoundError("data/benchmark.json not found.")

    evaluator = BenchmarkEvaluator()
    print("Running evaluation over benchmark dataset...")
    metrics = evaluator.evaluate_file(benchmark_file)

    report_text = metrics.summary_report()
    print(report_text)

    # Save empirical results
    results_json_path = Path("data/benchmark_results.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics.to_dict(), f, indent=2)

    report_path = Path("data/benchmark_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")

    print(f"Results saved to {results_json_path} and {report_path}")


if __name__ == "__main__":
    main()
