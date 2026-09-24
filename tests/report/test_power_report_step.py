"""Tests for the power report building step."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.experiment_execution.step.report_step.power.power_report_step import (
    PowerReportBuildingStep,
)
from pysatl_experiment.persistence.models.power import IPowerStorage, PowerModel, PowerQuery


BUILDER_PATH = "pysatl_experiment.experiment_execution.step.report_step.power.power_report_step.PowerReportBuilder"

SAMPLE_SIZE_CASES = [
    pytest.param([20, 10], [10, 20], id="unsorted"),
    pytest.param([100, 5, 50], [5, 50, 100], id="three-sizes"),
    pytest.param([7], [7], id="single-size"),
]

QUERY_CASES = [
    pytest.param(10, 0.05, id="size-10-alpha-005"),
    pytest.param(20, 0.01, id="size-20-alpha-001"),
    pytest.param(100, 0.1, id="size-100-alpha-01"),
]


@pytest.fixture()
def storage() -> MagicMock:
    """Build a power storage double."""
    return MagicMock(spec=IPowerStorage)


@pytest.fixture()
def step_factory(storage: MagicMock, mock_criterion_config, mock_alternative, results_path):
    """Build a factory creating report steps with overridable parameters."""

    def factory(**overrides):
        parameters = {
            "report_name": "power",
            "criteria_config": [mock_criterion_config],
            "significance_levels": [0.05],
            "alternatives": [mock_alternative],
            "sample_sizes": [10],
            "monte_carlo_count": 100,
            "result_storage": storage,
            "results_path": results_path,
            "with_chart": ReportMode.WITH_CHART,
        }
        parameters.update(overrides)

        return PowerReportBuildingStep(**parameters)

    return factory


def make_power_model(results: list[bool], sample_size: int = 10) -> PowerModel:
    """Build a stored power result."""
    return PowerModel(
        experiment_id=1,
        criterion_code="KS_",
        criterion_parameters=[],
        sample_size=sample_size,
        alternative_code="NORMAL",
        alternative_parameters={"mean": 0.0, "std": 1.0},
        monte_carlo_count=100,
        significance_level=0.05,
        results_criteria=results,
    )


# Checks that every constructor argument is stored on the step.
def test_init_stores_attributes(step_factory, storage, mock_criterion_config, mock_alternative, results_path) -> None:
    step = step_factory(
        significance_levels=[0.05, 0.01],
        sample_sizes=[20, 10],
        monte_carlo_count=42,
        with_chart=ReportMode.WITHOUT_CHART,
    )

    assert step.report_name == "power"
    assert step.criteria_config == [mock_criterion_config]
    assert step.significance_levels == [0.05, 0.01]
    assert step.alternatives == [mock_alternative]
    assert step.monte_carlo_count == 42
    assert step.result_storage is storage
    assert step.results_path == results_path
    assert step.with_chart is ReportMode.WITHOUT_CHART


# Checks that sample sizes are sorted during initialization.
@pytest.mark.parametrize(("sample_sizes", "expected_sizes"), SAMPLE_SIZE_CASES)
def test_init_sorts_sample_sizes(step_factory, sample_sizes: list[int], expected_sizes: list[int]) -> None:
    assert step_factory(sample_sizes=sample_sizes).sizes == expected_sizes


# Checks that run collects statistics and delegates report building to the builder.
@pytest.mark.parametrize("chart_mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
@patch(BUILDER_PATH)
def test_run_builds_report(mock_builder_cls, step_factory, storage, results_path, chart_mode) -> None:
    storage.get_data.return_value = make_power_model([True, False])

    step = step_factory(sample_sizes=[20, 10], with_chart=chart_mode)
    step.run()

    mock_builder_cls.assert_called_once_with(
        report_name="power",
        criteria_config=step.criteria_config,
        sample_sizes=[10, 20],
        alternatives=step.alternatives,
        significance_levels=step.significance_levels,
        power_result={"KS_": {(DistributionType.NORMAL, 0.05): {10: [True, False], 20: [True, False]}}},
        results_path=results_path,
        with_chart=chart_mode,
    )
    mock_builder_cls.return_value.build.assert_called_once_with()


# Checks that run propagates the error raised for missing storage results.
def test_run_propagates_missing_result_error(step_factory, storage) -> None:
    storage.get_data.return_value = None

    with pytest.raises(ValueError, match="Power for query"):
        step_factory().run()


# Checks that statistics are grouped by criterion, alternative and sample size.
def test_collect_statistics_groups_results(step_factory, storage) -> None:
    storage.get_data.return_value = make_power_model([True, False])

    step = step_factory(significance_levels=[0.05], sample_sizes=[10, 20])

    assert step._collect_statistics() == {
        "KS_": {(DistributionType.NORMAL, 0.05): {10: [True, False], 20: [True, False]}}
    }


# Checks that every criterion/alternative/level/size combination is queried.
@pytest.mark.parametrize(
    ("criteria_count", "alternatives_count", "sizes_count", "levels_count"),
    [(1, 1, 1, 1), (2, 2, 3, 2)],
)
def test_collect_statistics_queries_every_combination(
    step_factory, storage, criteria_count, alternatives_count, sizes_count, levels_count
) -> None:
    storage.get_data.return_value = make_power_model([True])
    criteria = [
        MagicMock(criterion_code=f"CRIT_{index}_", criterion=MagicMock(parameters=[]))
        for index in range(criteria_count)
    ]
    alternatives = [
        MagicMock(distribution_type=distribution, parameters={"p": 1.0})
        for distribution in list(DistributionType)[:alternatives_count]
    ]
    step = step_factory(
        criteria_config=criteria,
        alternatives=alternatives,
        sample_sizes=list(range(10, 10 * (sizes_count + 1), 10)),
        significance_levels=[0.05 * (index + 1) for index in range(levels_count)],
    )

    data = step._collect_statistics()

    assert storage.get_data.call_count == criteria_count * alternatives_count * sizes_count * levels_count
    assert len(data) == criteria_count
    assert all(len(levels) == alternatives_count * levels_count for levels in data.values())
    assert all(len(sizes) == sizes_count for levels in data.values() for sizes in levels.values())


# Checks that a power result query is built from the criterion, alternative and level.
@pytest.mark.parametrize(("sample_size", "significance_level"), QUERY_CASES)
def test_get_power_result_from_storage_builds_query(
    step_factory, storage, mock_criterion_config, mock_alternative, sample_size, significance_level
) -> None:
    storage.get_data.return_value = make_power_model([True], sample_size=sample_size)
    step = step_factory(monte_carlo_count=7)

    result = step._get_power_result_from_storage(
        criterion_config=mock_criterion_config,
        sample_size=sample_size,
        alternative=mock_alternative,
        significance_level=significance_level,
    )

    storage.get_data.assert_called_once_with(
        PowerQuery(
            criterion_code="KS_",
            criterion_parameters=[],
            sample_size=sample_size,
            alternative_code=DistributionType.NORMAL,
            alternative_parameters={"mean": 0.0, "std": 1.0},
            monte_carlo_count=7,
            significance_level=significance_level,
        )
    )
    assert result == [True]


# Checks that a missing power result raises a ValueError mentioning the query.
def test_get_power_result_from_storage_raises_when_missing(
    step_factory, storage, mock_criterion_config, mock_alternative
) -> None:
    storage.get_data.return_value = None
    step = step_factory()

    with pytest.raises(ValueError, match="Power for query"):
        step._get_power_result_from_storage(
            criterion_config=mock_criterion_config,
            sample_size=10,
            alternative=mock_alternative,
            significance_level=0.05,
        )
