"""Tests for the time complexity measurement worker."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from pysatl_experiment.experiment_execution.step.execution_step.time_complexity import time_complexity_worker
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.time_complexity_worker import (
    TimeComplexityWorker,
    TimeComplexityWorkerResult,
)


# Checks that the constructor stores every provided argument.
def test_constructor_stores_arguments() -> None:
    statistics = MagicMock()
    samples = [[1.0], [2.0, 3.0]]

    worker = TimeComplexityWorker(statistics, samples)

    assert worker.statistics is statistics
    assert worker.sample_data is samples


# Checks that execute measures exactly one duration per sample.
def test_execute_returns_one_time_per_sample() -> None:
    statistics = MagicMock()
    samples = [[1.0, 2.0], [3.0], [4.0, 5.0, 6.0]]

    result = TimeComplexityWorker(statistics, samples).execute()

    assert isinstance(result, TimeComplexityWorkerResult)
    assert len(result.results_times) == len(samples)
    assert all(isinstance(value, float) for value in result.results_times)
    assert all(value >= 0.0 for value in result.results_times)
    assert statistics.execute_statistic.call_count == len(samples)


# Checks that recorded times equal the difference between consecutive timer reads.
def test_execute_records_elapsed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    statistics = MagicMock()
    readings = iter([1.0, 3.0, 10.0, 11.5])
    monkeypatch.setattr(time_complexity_worker, "perf_counter", lambda: next(readings))

    result = TimeComplexityWorker(statistics, [[1.0], [2.0]]).execute()

    assert result.results_times == [2.0, 1.5]


# Checks that each sample is forwarded to the statistic as the rvs argument.
def test_execute_forwards_samples_to_statistic() -> None:
    statistics = MagicMock()
    samples = [[1.0, 2.0], [3.0, 4.0]]

    TimeComplexityWorker(statistics, samples).execute()

    assert statistics.execute_statistic.call_args_list == [
        call(rvs=[1.0, 2.0]),
        call(rvs=[3.0, 4.0]),
    ]


# Checks that an empty sample list yields no times and no statistic calls.
def test_execute_without_samples_returns_empty_result() -> None:
    statistics = MagicMock()

    result = TimeComplexityWorker(statistics, []).execute()

    assert result.results_times == []
    statistics.execute_statistic.assert_not_called()


# Checks that the result length always matches the number of samples.
@pytest.mark.parametrize("sample_count", [1, 2, 4, 8])
def test_execute_result_length_matches_sample_count(sample_count: int) -> None:
    statistics = MagicMock()
    samples = [[float(index)] for index in range(sample_count)]

    result = TimeComplexityWorker(statistics, samples).execute()

    assert len(result.results_times) == sample_count


# Checks that the statistic return value does not affect the recorded durations.
def test_execute_ignores_statistic_return_value(monkeypatch: pytest.MonkeyPatch) -> None:
    statistics = MagicMock()
    statistics.execute_statistic.side_effect = [None, "ignored", 123]
    readings = iter([0.0, 1.0, 1.0, 2.5, 2.5, 4.0])
    monkeypatch.setattr(time_complexity_worker, "perf_counter", lambda: next(readings))

    result = TimeComplexityWorker(statistics, [[1.0], [2.0], [3.0]]).execute()

    assert result.results_times == [1.0, 1.5, 1.5]


# Checks that the result dataclass stores times and supports equality.
def test_result_dataclass_equality() -> None:
    assert TimeComplexityWorkerResult(results_times=[0.1]) == TimeComplexityWorkerResult(results_times=[0.1])
    assert TimeComplexityWorkerResult(results_times=[0.1]) != TimeComplexityWorkerResult(results_times=[0.2])
