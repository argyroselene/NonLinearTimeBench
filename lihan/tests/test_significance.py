import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from metrics.significance import bootstrap_ci, wilcoxon_test


def test_wilcoxon_detects_a_consistent_positive_shift():
    a = [0.9, 0.85, 0.95, 0.88, 0.92, 0.91, 0.87, 0.93]
    b = [0.6, 0.55, 0.65, 0.58, 0.62, 0.61, 0.57, 0.63]
    result = wilcoxon_test(a, b)
    assert result["n"] == 8
    assert result["mean_diff"] == pytest.approx(0.3, abs=1e-9)
    assert result["p_value"] < 0.05


def test_wilcoxon_reports_no_effect_when_all_pairs_are_tied():
    a = [0.5, 0.6, 0.7]
    result = wilcoxon_test(a, list(a))
    assert result == {"n": 3, "statistic": 0.0, "p_value": 1.0, "mean_diff": 0.0}


def test_wilcoxon_finds_no_significant_difference_in_noise_around_zero():
    a = [0.5, 0.52, 0.48, 0.51, 0.49, 0.50]
    b = [0.5, 0.49, 0.52, 0.48, 0.51, 0.50]
    result = wilcoxon_test(a, b)
    assert result["p_value"] > 0.05


def test_wilcoxon_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        wilcoxon_test([1, 2], [1, 2, 3])


def test_wilcoxon_rejects_empty_input():
    with pytest.raises(ValueError):
        wilcoxon_test([], [])


def test_bootstrap_ci_contains_the_sample_mean():
    values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    ci = bootstrap_ci(values, n_resamples=2000, seed=42)
    assert ci["low"] <= ci["point_estimate"] <= ci["high"]
    assert ci["point_estimate"] == pytest.approx(sum(values) / len(values))
    assert ci["n_resamples"] == 2000


def test_bootstrap_ci_is_narrower_for_low_variance_data_than_high_variance_data():
    low_variance = [0.5] * 20 + [0.51, 0.49]
    high_variance = [0.0, 1.0] * 11
    low_ci = bootstrap_ci(low_variance, n_resamples=2000, seed=1)
    high_ci = bootstrap_ci(high_variance, n_resamples=2000, seed=1)
    assert (low_ci["high"] - low_ci["low"]) < (high_ci["high"] - high_ci["low"])


def test_bootstrap_ci_rejects_empty_input():
    with pytest.raises(ValueError):
        bootstrap_ci([])
