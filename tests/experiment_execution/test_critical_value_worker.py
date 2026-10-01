"""Tests for the critical value computation worker."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest
from numpy import float64

from pysatl_experiment.experiment_execution.step.execution_step.critical_value.critical_value_worker import (
    CriticalValueWorker,
    CriticalValueWorkerResult,
)


# Checks that the constructor stores every provided argument.
def test_constructor_stores_arguments() -> None:
    statistics = MagicMock()
    samples = [[1.0], [2.0, 3.0]]

    worker = CriticalValueWorker(statistics, samples)

    assert worker.statistics is statistics
    assert worker.sample_data is samples


# Checks that execute computes exactly one statistic value per sample.
def test_execute_returns_statistic_per_sample() -> None:
    statistics = MagicMock()
    statistics.execute_statistic.side_effect = [1.5, 2.5, 3.5]
    samples = [[1.0], [2.0], [3.0]]

    result = CriticalValueWorker(statistics, samples).execute()

    assert isinstance(result, CriticalValueWorkerResult)
    assert result.results_statistics == [1.5, 2.5, 3.5]
    assert statistics.execute_statistic.call_count == 3


# Checks that each sample is forwarded to the statistic as the rvs argument.
def test_execute_forwards_samples_to_statistic() -> None:
    statistics = MagicMock()
    statistics.execute_statistic.side_effect = [0.1, 0.2]

    CriticalValueWorker(statistics, [[1.0, 2.0], [3.0]]).execute()

    assert statistics.execute_statistic.call_args_list == [
        call(rvs=[1.0, 2.0]),
        call(rvs=[3.0]),
    ]


# Checks that an empty sample list yields no results and no statistic calls.
def test_execute_without_samples_returns_empty_result() -> None:
    statistics = MagicMock()

    result = CriticalValueWorker(statistics, []).execute()

    assert result.results_statistics == []
    statistics.execute_statistic.assert_not_called()


# Checks that the result length always matches the number of samples.
@pytest.mark.parametrize("sample_count", [1, 2, 5])
def test_execute_result_length_matches_sample_count(sample_count: int) -> None:
    statistics = MagicMock()
    statistics.execute_statistic.side_effect = [float(index) for index in range(sample_count)]
    samples = [[float(index)] for index in range(sample_count)]

    result = CriticalValueWorker(statistics, samples).execute()

    assert result.results_statistics == [float(index) for index in range(sample_count)]


# Checks that numpy scalars returned by the statistic are preserved in the result.
def test_execute_preserves_numpy_values() -> None:
    statistics = MagicMock()
    statistics.execute_statistic.side_effect = [float64(1.25)]

    result = CriticalValueWorker(statistics, [[1.0]]).execute()

    assert isinstance(result.results_statistics[0], float64)
    assert result.results_statistics == [float64(1.25)]


# Checks that the result dataclass stores statistics and supports equality.
def test_result_dataclass_equality() -> None:
    assert CriticalValueWorkerResult(results_statistics=[1.0]) == CriticalValueWorkerResult(results_statistics=[1.0])
    assert CriticalValueWorkerResult(results_statistics=[1.0]) != CriticalValueWorkerResult(results_statistics=[2.0])
