"""Tests for the time complexity report building step."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_statistic import (
    TimeComplexityReportStatistic,
)
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_step import (
    TimeComplexityReportBuildingStep,
)
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_step_context import (  # noqa: E501
    TimeComplexityReportStepContext,
)
from pysatl_experiment.persistence.models.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
    TimeComplexityQuery,
)


STEP_MODULE = "pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_step"
BUILDER_PATH = f"{STEP_MODULE}.TimeComplexityReportBuilder"

SAMPLE_SIZE_CASES = [
    pytest.param([20, 10], [10, 20], id="unsorted"),
    pytest.param([100, 5, 50], [5, 50, 100], id="three-sizes"),
    pytest.param([7], [7], id="single-size"),
]


@pytest.fixture()
def storage() -> MagicMock:
    """Build a time complexity storage double."""
    return MagicMock(spec=ITimeComplexityStorage)


@pytest.fixture()
def builder():
    """Patch the time complexity report builder and return the replacement class."""
    with patch(BUILDER_PATH) as mock_builder:
        yield mock_builder


@pytest.fixture()
def step_factory(storage: MagicMock, mock_criterion_config, results_path):
    """Build a factory creating report steps with overridable context values."""

    def factory(**overrides: Any) -> TimeComplexityReportBuildingStep:
        parameters: dict[str, Any] = {
            "experiment_name": "tc_exp",
            "report_name": "tc",
            "criteria_config": [mock_criterion_config],
            "sample_sizes": [10],
            "monte_carlo_count": 100,
            "samples_count": 50,
            "results_path": results_path,
            "report_mode": ReportMode.WITH_CHART,
            "data_list": [],
        }
        parameters.update(overrides)

        return TimeComplexityReportBuildingStep(TimeComplexityReportStepContext(**parameters), storage)

    return factory


def make_times(experiment_name: str = "tc_exp", sample_size: int = 10) -> TimeComplexityModel:
    """Build a stored time complexity result."""
    return TimeComplexityModel(
        experiment_name=experiment_name,
        criterion_code="KS_",
        criterion_parameters=[],
        sample_size=sample_size,
        samples_count=50,
        results_times=[0.1, 0.2, 0.3],
    )


# Checks that the step copies every context value onto itself.
def test_init_stores_context_attributes(step_factory, storage, mock_criterion_config, results_path) -> None:
    step = step_factory(
        sample_sizes=[20, 10],
        samples_count=42,
        report_mode=ReportMode.WITHOUT_CHART,
    )

    assert step.experiment_name == "tc_exp"
    assert step.criteria_config == [mock_criterion_config]
    assert step.monte_carlo_count == 100
    assert step.results_path == results_path
    assert step.with_chart is ReportMode.WITHOUT_CHART
    assert step.result_storage is storage
    assert step.sizes == [10, 20]
    assert step.ctx.samples_count == 42


# Checks that sample sizes are sorted during initialization.
@pytest.mark.parametrize(("sample_sizes", "expected_sizes"), SAMPLE_SIZE_CASES)
def test_init_sorts_sample_sizes(step_factory, sample_sizes: list[int], expected_sizes: list[int]) -> None:
    assert step_factory(sample_sizes=sample_sizes).sizes == expected_sizes


# Checks that run collects statistics and builds the report.
def test_run_builds_report_with_statistics(step_factory, storage, builder) -> None:
    storage.get_data.return_value = make_times()
    step = step_factory(sample_sizes=[10, 20])

    step.run()

    builder.assert_called_once()
    kwargs = builder.call_args.kwargs
    assert kwargs["report_name"] == "tc"
    assert kwargs["sample_sizes"] == [10, 20]
    assert kwargs["results_path"] == step.results_path
    assert kwargs["report_mode"] is ReportMode.WITH_CHART
    assert isinstance(kwargs["statistic"], TimeComplexityReportStatistic)
    assert kwargs["statistic"].as_dict() == {"KS_": [(10, pytest.approx(0.2)), (20, pytest.approx(0.2))]}
    builder.return_value.build.assert_called_once_with()


# Checks that the mean execution time is stored per criterion and sample size.
def test_collect_statistics_averages_times(step_factory, storage, mock_criterion_config) -> None:
    storage.get_data.return_value = make_times()
    step = step_factory(criteria_config=[mock_criterion_config], sample_sizes=[10, 20])

    statistic = step._collect_statistics()

    assert statistic.as_dict() == {"KS_": [(10, pytest.approx(0.2)), (20, pytest.approx(0.2))]}


# Checks that every criterion and sample size combination is queried.
@pytest.mark.parametrize(("criteria_count", "sizes_count"), [(1, 1), (2, 3)])
def test_collect_statistics_queries_every_combination(
    step_factory, storage, criteria_count: int, sizes_count: int
) -> None:
    storage.get_data.return_value = make_times()
    criteria = [
        MagicMock(criterion_code=f"CRIT_{index}_", criterion=MagicMock(parameters=[]))
        for index in range(criteria_count)
    ]
    step = step_factory(criteria_config=criteria, sample_sizes=[10 * (index + 1) for index in range(sizes_count)])

    statistic = step._collect_statistics()

    assert storage.get_data.call_count == criteria_count * sizes_count
    assert len(statistic.as_dict()) == criteria_count
    assert all(len(points) == sizes_count for points in statistic.as_dict().values())


# Checks that an empty timing list is skipped instead of averaging it.
def test_collect_statistics_skips_empty_times(step_factory, storage, mock_criterion_config) -> None:
    storage.get_data.return_value = make_times()
    storage.get_data.return_value.results_times = []
    step = step_factory(criteria_config=[mock_criterion_config], sample_sizes=[10])

    statistic = step._collect_statistics()

    assert statistic.as_dict() == {}


# Checks that the timing query is built from the experiment, criterion and sample size.
@pytest.mark.parametrize(("sample_size", "samples_count"), [(10, 50), (100, 20), (7, 1)])
def test_get_times_from_storage_builds_query(step_factory, storage, sample_size: int, samples_count: int) -> None:
    storage.get_data.return_value = make_times(sample_size=sample_size)
    step = step_factory()

    times = step._get_times_from_storage(
        experiment_name="tc_exp",
        criterion_code="KS_",
        criterion_parameters=[],
        sample_size=sample_size,
        samples_count=samples_count,
    )

    storage.get_data.assert_called_once_with(
        TimeComplexityQuery(
            experiment_name="tc_exp",
            criterion_code="KS_",
            criterion_parameters=[],
            sample_size=sample_size,
            samples_count=samples_count,
        )
    )
    assert times == [0.1, 0.2, 0.3]


# Checks that a missing timing result raises a ValueError mentioning the query.
def test_get_times_from_storage_raises_when_missing(step_factory, storage) -> None:
    storage.get_data.return_value = None
    step = step_factory()

    with pytest.raises(ValueError, match="Times for query"):
        step._get_times_from_storage(
            experiment_name="tc_exp",
            criterion_code="KS_",
            criterion_parameters=[],
            sample_size=10,
            samples_count=50,
        )
