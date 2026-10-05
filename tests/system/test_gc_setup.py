"""Tests for garbage collector tuning helpers."""

from unittest.mock import patch

from pysatl_experiment.system.gc_setup import gc_set_threshold


# Checks that CPython runs receive the tuned garbage collector thresholds.
def test_gc_set_threshold_applies_tuned_values_on_cpython() -> None:
    with (
        patch("pysatl_experiment.system.gc_setup.platform.python_implementation", return_value="CPython"),
        patch("pysatl_experiment.system.gc_setup.gc.set_threshold") as set_threshold,
    ):
        gc_set_threshold()

    set_threshold.assert_called_once_with(50_000, 500, 1000)


# Checks that non-CPython implementations keep their default thresholds untouched.
def test_gc_set_threshold_skips_non_cpython() -> None:
    with (
        patch("pysatl_experiment.system.gc_setup.platform.python_implementation", return_value="PyPy"),
        patch("pysatl_experiment.system.gc_setup.gc.set_threshold") as set_threshold,
    ):
        gc_set_threshold()

    set_threshold.assert_not_called()
