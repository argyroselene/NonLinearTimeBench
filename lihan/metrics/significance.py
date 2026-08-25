"""Paired-comparison statistics for the scaled-up dataset (PLAN_AND_STATUS.md M8).

At N=5 (the pilot set), a single test statistic is not meaningful -- the M3/M4
findings were reported as pilot-scale observations, not statistically validated
claims. At N=20+ (post scale-up), each hypothesis (H1/H2/H3, and the PCR/COC
repair effect) is a *paired* comparison -- two scores per story, computed from
the same gold graph -- so a paired non-parametric test (Wilcoxon signed-rank,
which makes no normality assumption and is standard for small-to-moderate paired
samples) plus a bootstrap confidence interval for effect-size context is the
right pairing of tools: the test says whether the direction is likely real, the
CI says how big and how uncertain the effect is.
"""

import random
import statistics
from collections.abc import Callable, Sequence

from scipy.stats import wilcoxon


def wilcoxon_test(paired_a: Sequence[float], paired_b: Sequence[float]) -> dict[str, float]:
    """Wilcoxon signed-rank test on two same-length sequences of per-story scores
    (paired by story, e.g. original vs. counterfactual AWT-F1).

    Returns {"n": int, "statistic": float, "p_value": float, "mean_diff": float}.
    `mean_diff` is mean(a) - mean(b); a positive value means `a` scored higher.
    Ties (a[i] == b[i] for every i) make the signed-rank statistic undefined, so
    that case is reported explicitly rather than raising or fabricating a value.
    """
    if len(paired_a) != len(paired_b):
        raise ValueError("paired_a and paired_b must be the same length")
    n = len(paired_a)
    if n == 0:
        raise ValueError("need at least one paired observation")

    diffs = [a - b for a, b in zip(paired_a, paired_b)]
    mean_diff = statistics.fmean(diffs)

    if all(d == 0 for d in diffs):
        return {"n": n, "statistic": 0.0, "p_value": 1.0, "mean_diff": 0.0}

    result = wilcoxon(paired_a, paired_b)
    return {"n": n, "statistic": float(result.statistic), "p_value": float(result.pvalue), "mean_diff": mean_diff}


def bootstrap_ci(
    values: Sequence[float],
    statistic_fn: Callable[[Sequence[float]], float] = statistics.fmean,
    n_resamples: int = 10000,
    confidence: float = 0.95,
    seed: int = 0,
) -> dict[str, float]:
    """Bootstrap confidence interval for `statistic_fn` over `values`, resampling
    stories with replacement -- the standard approach for effect-size uncertainty
    when N is too small to trust a normal-approximation interval.

    Returns {"point_estimate": float, "low": float, "high": float, "n_resamples": int}.
    """
    if len(values) == 0:
        raise ValueError("need at least one value")
    if n_resamples <= 0:
        raise ValueError("n_resamples must be positive")

    rng = random.Random(seed)
    point_estimate = statistic_fn(values)

    resample_stats = []
    for _ in range(n_resamples):
        resample = [rng.choice(values) for _ in values]
        resample_stats.append(statistic_fn(resample))
    resample_stats.sort()

    alpha = 1 - confidence
    low_idx = int((alpha / 2) * n_resamples)
    high_idx = int((1 - alpha / 2) * n_resamples) - 1
    low_idx = max(0, min(low_idx, n_resamples - 1))
    high_idx = max(0, min(high_idx, n_resamples - 1))

    return {
        "point_estimate": point_estimate,
        "low": resample_stats[low_idx],
        "high": resample_stats[high_idx],
        "n_resamples": n_resamples,
    }
