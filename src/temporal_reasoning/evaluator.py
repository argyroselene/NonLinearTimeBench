"""
Evaluation framework for temporal reasoning engine.
Computes accuracy, precision, recall, macro F1, consistency rate,
and explicit vs inferred relation accuracy across benchmark datasets.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from temporal_reasoning.relations import TemporalRelation, parse_relation
from temporal_reasoning.engine import TemporalReasoningEngine


@dataclass
class EvaluationMetrics:
    """Summary of benchmark evaluation metrics."""

    total_examples: int
    correct_predictions: int
    accuracy: float
    explicit_accuracy: float
    inferred_accuracy: float
    consistency_rate: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    category_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    detailed_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_examples": self.total_examples,
            "correct_predictions": self.correct_predictions,
            "accuracy": round(self.accuracy, 4),
            "explicit_accuracy": round(self.explicit_accuracy, 4),
            "inferred_accuracy": round(self.inferred_accuracy, 4),
            "consistency_rate": round(self.consistency_rate, 4),
            "precision_macro": round(self.precision_macro, 4),
            "recall_macro": round(self.recall_macro, 4),
            "f1_macro": round(self.f1_macro, 4),
            "category_breakdown": self.category_breakdown,
        }

    def summary_report(self) -> str:
        lines = [
            "==================================================",
            "          Temporal Reasoning Evaluation           ",
            "==================================================",
            f"Total Examples:          {self.total_examples}",
            f"Overall Accuracy:        {self.accuracy * 100:.1f}%",
            f"Explicit Accuracy:       {self.explicit_accuracy * 100:.1f}%",
            f"Inference Accuracy:      {self.inferred_accuracy * 100:.1f}%",
            f"Consistency Rate:        {self.consistency_rate * 100:.1f}%",
            f"Macro Precision:         {self.precision_macro:.3f}",
            f"Macro Recall:            {self.recall_macro:.3f}",
            f"Macro F1 Score:          {self.f1_macro:.3f}",
            "--------------------------------------------------",
            "Category Breakdown:",
        ]
        for cat, stats in sorted(self.category_breakdown.items()):
            acc = stats["accuracy"] * 100
            lines.append(f"  - {cat:<26}: {stats['correct']}/{stats['total']} ({acc:.1f}%)")
        lines.append("==================================================")
        return "\n".join(lines)


class BenchmarkEvaluator:
    """Evaluates TemporalReasoningEngine over standardized datasets."""

    def evaluate_file(self, json_path: Union[str, Path]) -> EvaluationMetrics:
        """Load benchmark file and run evaluation."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.evaluate_dataset(data)

    def evaluate_dataset(self, examples: List[Dict[str, Any]]) -> EvaluationMetrics:
        """Evaluate a list of benchmark example dictionaries."""
        total = len(examples)
        if total == 0:
            return EvaluationMetrics(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        correct = 0
        explicit_total = 0
        explicit_correct = 0
        inferred_total = 0
        inferred_correct = 0
        consistent_correct = 0

        # Confusion statistics per label
        true_positives: Dict[str, int] = {}
        false_positives: Dict[str, int] = {}
        false_negatives: Dict[str, int] = {}

        category_stats: Dict[str, Dict[str, int]] = {}
        detailed_results = []

        for ex in examples:
            cat = ex.get("category", "general")
            category_stats.setdefault(cat, {"total": 0, "correct": 0})
            category_stats[cat]["total"] += 1

            engine = TemporalReasoningEngine()
            for stmt in ex["statements"]:
                engine.add_statement(stmt)

            query_src, query_tgt = ex["query"]
            expected_raw = ex.get("expected")
            expected_rel = parse_relation(expected_raw).value if expected_raw else None
            expected_consistent = ex.get("is_consistent", True)

            # Check predicted consistency
            predicted_consistent = engine.is_consistent()
            if predicted_consistent == expected_consistent:
                consistent_correct += 1

            # Check predicted relation
            predicted_rel_enum = engine.query(query_src, query_tgt)
            predicted_rel = predicted_rel_enum.value if predicted_rel_enum else None

            # Determine whether prediction was explicit or inferred
            src_id = engine.graph._resolve_id(query_src)
            tgt_id = engine.graph._resolve_id(query_tgt)
            edges = engine.graph._adjacency.get(src_id, {}).get(tgt_id, [])
            matching_edge = next((e for e in edges if e.relation.value == predicted_rel), None)
            is_inferred = matching_edge.is_inferred if matching_edge else True

            # Evaluate correctness
            is_correct = False
            if not expected_consistent:
                # For contradiction examples, success means detecting the inconsistency
                is_correct = not predicted_consistent
            else:
                is_correct = (predicted_rel == expected_rel)

            if is_correct:
                correct += 1
                category_stats[cat]["correct"] += 1

            if expected_consistent and expected_rel:
                if is_inferred:
                    inferred_total += 1
                    if is_correct:
                        inferred_correct += 1
                else:
                    explicit_total += 1
                    if is_correct:
                        explicit_correct += 1

                # Update per-class metrics
                all_labels = {expected_rel}
                if predicted_rel:
                    all_labels.add(predicted_rel)
                for lbl in all_labels:
                    true_positives.setdefault(lbl, 0)
                    false_positives.setdefault(lbl, 0)
                    false_negatives.setdefault(lbl, 0)

                if predicted_rel == expected_rel:
                    true_positives[expected_rel] += 1
                else:
                    false_negatives[expected_rel] += 1
                    if predicted_rel:
                        false_positives[predicted_rel] += 1

            detailed_results.append({
                "id": ex["id"],
                "category": cat,
                "expected": expected_rel,
                "predicted": predicted_rel,
                "expected_consistent": expected_consistent,
                "predicted_consistent": predicted_consistent,
                "is_correct": is_correct,
                "is_inferred": is_inferred,
            })

        # Calculate metrics
        acc = correct / total
        exp_acc = (explicit_correct / explicit_total) if explicit_total > 0 else 1.0
        inf_acc = (inferred_correct / inferred_total) if inferred_total > 0 else 1.0
        cons_rate = consistent_correct / total

        # Macro P/R/F1
        labels = list(true_positives.keys())
        p_list, r_list, f1_list = [], [], []
        for lbl in labels:
            tp = true_positives[lbl]
            fp = false_positives.get(lbl, 0)
            fn = false_negatives.get(lbl, 0)
            p = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            r = tp / (tp + fn) if (tp + fn) > 0 else 1.0
            f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
            p_list.append(p)
            r_list.append(r)
            f1_list.append(f1)

        macro_p = sum(p_list) / len(p_list) if p_list else 1.0
        macro_r = sum(r_list) / len(r_list) if r_list else 1.0
        macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 1.0

        cat_breakdown = {}
        for c, st in category_stats.items():
            tot = st["total"]
            corr = st["correct"]
            cat_breakdown[c] = {
                "total": tot,
                "correct": corr,
                "accuracy": round(corr / tot, 4) if tot > 0 else 0.0,
            }

        return EvaluationMetrics(
            total_examples=total,
            correct_predictions=correct,
            accuracy=acc,
            explicit_accuracy=exp_acc,
            inferred_accuracy=inf_acc,
            consistency_rate=cons_rate,
            precision_macro=macro_p,
            recall_macro=macro_r,
            f1_macro=macro_f1,
            category_breakdown=cat_breakdown,
            detailed_results=detailed_results,
        )
