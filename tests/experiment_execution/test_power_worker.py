"""Tests for the power analysis worker."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pysatl_experiment.experiment_execution.step.execution_step.power import power_worker
from pysatl_experiment.experiment_execution.step.execution_step.power.power_worker import PowerWorker, PowerWorkerResult


@pytest.fixture()
def storage_factory(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the limit distribution storage with a controllable factory."""
    factory = MagicMock(name="AlchemyLimitDistributionStorage")
    monkeypatch.setattr(power_worker, "AlchemyLimitDistributionStorage", factory)
    return factory


@pytest.fixture()
def gof_factory(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the goodness-of-fit test with a controllable factory."""
    factory = MagicMock(name="GoodnessOfFitTest")
    monkeypatch.setattr(power_worker, "GoodnessOfFitTest", factory)
    return factory


@pytest.fixture()
def decision_method_factory(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the critical value decision method with a controllable factory."""
    factory = MagicMock(name="CriticalValueDecisionMethod")
    monkeypatch.setattr(power_worker, "CriticalValueDecisionMethod", factory)
    return factory


def make_worker(
    sample_data: list[list[float]] | None = None,
    significance_level: float = 0.05,
    storage_connection: str = "sqlite:///cv.sqlite",
    statistics: MagicMock | None = None,
) -> PowerWorker:
    """Build a power worker with sensible defaults."""
    return PowerWorker(
        statistics=statistics if statistics is not None else MagicMock(),
        sample_data=[[1.0, 2.0], [3.0, 4.0]] if sample_data is None else sample_data,
        significance_level=significance_level,
        storage_connection=storage_connection,
    )


# Checks that the constructor stores every provided argument.
def test_constructor_stores_arguments() -> None:
    statistics = MagicMock()
    samples = [[1.0], [2.0, 3.0]]

    worker = PowerWorker(statistics, samples, 0.01, "sqlite:///db.sqlite")

    assert worker.statistics is statistics
    assert worker.sample_data is samples
    assert worker.significance_level == 0.01
    assert worker.storage_connection == "sqlite:///db.sqlite"


# Checks that execute returns a Boolean rejection flag for every sample.
def test_execute_returns_rejection_flag_per_sample(
    storage_factory: MagicMock, gof_factory: MagicMock, decision_method_factory: MagicMock
) -> None:
    gof_factory.return_value.test.side_effect = [
        SimpleNamespace(rejected=True),
        SimpleNamespace(rejected=False),
    ]

    result = make_worker().execute()

    assert isinstance(result, PowerWorkerResult)
    assert result.results_criteria == [True, False]


# Checks that execute initializes storage and builds the test and decision method.
def test_execute_wires_dependencies(
    storage_factory: MagicMock, gof_factory: MagicMock, decision_method_factory: MagicMock
) -> None:
    gof_factory.return_value.test.return_value = SimpleNamespace(rejected=True)
    statistics = MagicMock()

    make_worker(sample_data=[[1.0, 2.0]], statistics=statistics).execute()

    storage_factory.assert_called_once_with("sqlite:///cv.sqlite")
    storage_factory.return_value.init.assert_called_once_with()
    gof_factory.assert_called_once_with(statistic=statistics)
    assert gof_factory.return_value.test.call_count == 1
    args = gof_factory.return_value.test.call_args.args
    assert args[0] == [1.0, 2.0]
    assert args[1] == 0.05
    assert args[2] is decision_method_factory.return_value


# Checks that execute with no samples returns an empty result without testing.
def test_execute_without_samples_returns_empty_result(
    storage_factory: MagicMock, gof_factory: MagicMock, decision_method_factory: MagicMock
) -> None:
    result = make_worker(sample_data=[]).execute()

    assert result.results_criteria == []
    gof_factory.return_value.test.assert_not_called()
    storage_factory.return_value.init.assert_called_once_with()


# Checks that execute produces exactly one flag per sample for varying counts.
@pytest.mark.parametrize("sample_count", [1, 3, 5])
def test_execute_result_length_matches_sample_count(
    storage_factory: MagicMock,
    gof_factory: MagicMock,
    decision_method_factory: MagicMock,
    sample_count: int,
) -> None:
    gof_factory.return_value.test.return_value = SimpleNamespace(rejected=True)
    samples = [[float(index)] for index in range(sample_count)]

    result = make_worker(sample_data=samples).execute()

    assert len(result.results_criteria) == sample_count
    assert all(isinstance(flag, bool) for flag in result.results_criteria)


# Checks that the result dataclass stores flags and supports equality.
def test_result_dataclass_equality() -> None:
    assert PowerWorkerResult(results_criteria=[True, False]) == PowerWorkerResult(results_criteria=[True, False])
    assert PowerWorkerResult(results_criteria=[True]) != PowerWorkerResult(results_criteria=[False])
