"""The direct one-shot baseline (plan section 4A): a single prompt asking the
model for thread labels, global order, and convergence points all at once, with
no intermediate graph structure and no deterministic post-processing.
"""

from pipeline.prompts import direct_baseline_prompt
from pipeline.schemas import DIRECT_BASELINE_SCHEMA


def run_direct_baseline(passage, llm_client):
    """`passage` is a list of sentence strings (index 0 = sentence 1 = "s1")."""
    result = llm_client.complete(direct_baseline_prompt(passage), DIRECT_BASELINE_SCHEMA)
    return {
        "events": result["events"],
        "global_order": result["global_order"],
        "convergence_points": result["convergence_points"],
    }
