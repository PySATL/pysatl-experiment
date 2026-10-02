"""Stable generator codes retain the configured parameter semantics."""

import pytest

from pysatl_experiment.utils.generator_code import make_generator_code


def test_codes_sort_names_normalize_numbers_and_preserve_ranges():
    assert make_generator_code("normal", {"var": 1, "mean": [0, 1]}) == "normal_mean_[0.0,1.0]_var_1.0"
    assert make_generator_code("normal", {"mean": [-0.0, 1.0], "var": 1.0}) == "normal_mean_[0.0,1.0]_var_1.0"
    assert make_generator_code("normal", {"mean": 0, "var": 1}) == "normal_mean_0.0_var_1.0"
    assert make_generator_code("normal", {"mean": [0, 0]}) != make_generator_code("normal", {"mean": 0})


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), [], [0], [0, 1, 2], [2, 1], [0, float("inf")]])
def test_invalid_parameter_spec_is_rejected(value):
    with pytest.raises(ValueError):
        make_generator_code("normal", {"mean": value})
