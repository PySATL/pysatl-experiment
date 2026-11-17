"""Tests for the power analysis worker."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pysatl_experiment.experiment_execution.step.execution_step.power import power_worker
from pysatl_experiment.experiment_execution.step.execution_step.power.power_worker import PowerWorker, PowerWorkerResult


@pytest.fixture()
def cv_storage() -> MagicMock:
    """Return a mock limit distribution storage with a preloaded model."""
    storage = MagicMock(name="ILimitDistributionStorage")
    storage.get_data_for_cv.return_value = MagicMock(results_statistics=[0.1, 0.2, 0.3])
    return storage


@pytest.fixture()
def factory_cls(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the alternative factory lookup with a controllable mock."""
    mock_cls = MagicMock(name="AbstractAlternativeFactory")
    monkeypatch.setattr(power_worker, "AbstractAlternativeFactory", mock_cls)
    return mock_cls


def make_worker(
    sample_data: list[list[float]] | None = None,
    significance_level: float = 0.05,
    storage: MagicMock | None = None,
    statistics: MagicMock | None = None,
) -> PowerWorker:
    """Build a power worker with sensible defaults."""
    return PowerWorker(
        statistics=statistics if statistics is not None else MagicMock(),
        sample_data=[[1.0, 2.0], [3.0, 4.0]] if sample_data is None else sample_data,
        significance_level=significance_level,
        limit_distribution_storage=storage if storage is not None else MagicMock(),
    )


# Checks that the constructor stores every provided argument.
def test_constructor_stores_arguments() -> None:
    statistics = MagicMock()
    samples = [[1.0], [2.0, 3.0]]
    storage = MagicMock()

    worker = PowerWorker(statistics, samples, 0.01, storage)

    assert worker.statistics is statistics
    assert worker.sample_data is samples
    assert worker.significance_level == 0.01
    assert worker.limit_distribution_storage is storage


# Checks that execute returns a Boolean rejection flag for every sample.
def test_execute_returns_rejection_flag_per_sample(cv_storage: MagicMock, factory_cls: MagicMock) -> None:
    region = factory_cls.get_concrete_factory.return_value.get_critical_area.return_value
    region.contains.side_effect = [True, False]

    result = make_worker(storage=cv_storage).execute()

    assert isinstance(result, PowerWorkerResult)
    assert result.results_criteria == [False, True]


# Checks that execute queries the storage and wires the alternative factory.
def test_execute_wires_dependencies(cv_storage: MagicMock, factory_cls: MagicMock) -> None:
    statistics = MagicMock()
    statistics.code.return_value = "KS"

    make_worker(sample_data=[[1.0, 2.0]], storage=cv_storage, statistics=statistics).execute()

    query = cv_storage.get_data_for_cv.call_args.args[0]
    assert query.criterion_code == "KS"
    assert query.sample_size == 2

    factory_cls.get_concrete_factory.assert_called_once_with(statistics.alternative.return_value.type.return_value)
    factory = factory_cls.get_concrete_factory.return_value
    factory.get_critical_value_calculator.return_value.calculate.assert_called_once_with(
        cv_storage.get_data_for_cv.return_value.results_statistics, 0.05
    )
    statistics.execute_statistic.assert_called_once_with([1.0, 2.0])


# Checks that a missing limit distribution is reported with criterion and size.
def test_execute_raises_when_limit_distribution_missing(factory_cls: MagicMock) -> None:
    storage = MagicMock()
    storage.get_data_for_cv.return_value = None
    statistics = MagicMock()
    statistics.code.return_value = "KS"

    with pytest.raises(ValueError, match="Limit distribution for KS at n=2 not found"):
        make_worker(sample_data=[[1.0, 2.0]], storage=storage, statistics=statistics).execute()

    factory_cls.get_concrete_factory.assert_not_called()


# Checks that execute with no samples returns an empty result without querying storage.
def test_execute_without_samples_returns_empty_result() -> None:
    storage = MagicMock()

    result = make_worker(sample_data=[], storage=storage).execute()

    assert result.results_criteria == []
    storage.get_data_for_cv.assert_not_called()


# Checks that execute produces exactly one flag per sample for varying counts.
@pytest.mark.parametrize("sample_count", [1, 3, 5])
def test_execute_result_length_matches_sample_count(
    cv_storage: MagicMock, factory_cls: MagicMock, sample_count: int
) -> None:
    region = factory_cls.get_concrete_factory.return_value.get_critical_area.return_value
    region.contains.return_value = False
    samples = [[float(index)] for index in range(sample_count)]

    result = make_worker(sample_data=samples, storage=cv_storage).execute()

    assert len(result.results_criteria) == sample_count
    assert all(isinstance(flag, bool) for flag in result.results_criteria)


# Checks that the result dataclass stores flags and supports equality.
def test_result_dataclass_equality() -> None:
    assert PowerWorkerResult(results_criteria=[True, False]) == PowerWorkerResult(results_criteria=[True, False])
    assert PowerWorkerResult(results_criteria=[True]) != PowerWorkerResult(results_criteria=[False])
