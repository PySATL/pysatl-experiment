"""Tests for the critical value report building step."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pysatl_criterion.persistence.models.limit_distribution import (
    ILimitDistributionStorage,
    LimitDistributionModel,
    LimitDistributionQuery,
)

from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.experiment_execution.step.report_step.critical_value.critical_value_report_step import (
    CriticalValueReportBuildingStep,
)


STEP_MODULE = "pysatl_experiment.experiment_execution.step.report_step.critical_value.critical_value_report_step"
BUILDER_PATH = f"{STEP_MODULE}.CriticalValueReportBuilder"
CALCULATOR_PATH = f"{STEP_MODULE}.LeftCriticalValueCalculator"

SAMPLE_SIZE_CASES = [
    pytest.param([20, 10], [10, 20], id="unsorted"),
    pytest.param([100, 5, 50], [5, 50, 100], id="three-sizes"),
    pytest.param([7], [7], id="single-size"),
]


@pytest.fixture()
def storage() -> MagicMock:
    """Build a limit distribution storage double."""
    return MagicMock(spec=ILimitDistributionStorage)


@pytest.fixture()
def builder():
    """Patch the critical value report builder and return the replacement class."""
    with patch(BUILDER_PATH) as mock_builder:
        yield mock_builder


@pytest.fixture()
def calculator():
    """Patch the critical value calculator, echoing the level as the critical value."""
    with patch(CALCULATOR_PATH) as mock_calculator:
        mock_calculator.return_value.calculate.side_effect = lambda distribution, level: level
        yield mock_calculator


@pytest.fixture()
def step_factory(storage: MagicMock, mock_criterion_config, results_path):
    """Build a factory creating report steps with overridable parameters."""

    def factory(**overrides: Any) -> CriticalValueReportBuildingStep:
        parameters: dict[str, Any] = {
            "report_name": "cv",
            "criteria_config": [mock_criterion_config],
            "significance_levels": [0.05],
            "sample_sizes": [10],
            "monte_carlo_count": 100,
            "result_storage": storage,
            "results_path": results_path,
            "with_chart": ReportMode.WITH_CHART,
        }
        parameters.update(overrides)

        return CriticalValueReportBuildingStep(**parameters)

    return factory


def make_limit_distribution(criterion_code: str = "KS_", sample_size: int = 10) -> LimitDistributionModel:
    """Build a stored limit distribution result."""
    return LimitDistributionModel(
        experiment_id=1,
        criterion_code=criterion_code,
        criterion_parameters=[],
        sample_size=sample_size,
        monte_carlo_count=100,
        results_statistics=[0.1, 0.2, 0.3],
    )


# Checks that every constructor argument is stored on the step.
def test_init_stores_attributes(step_factory, storage, mock_criterion_config, results_path) -> None:
    step = step_factory(
        significance_levels=[0.05, 0.01],
        sample_sizes=[20, 10],
        monte_carlo_count=42,
        with_chart=ReportMode.WITHOUT_CHART,
    )

    assert step.report_name == "cv"
    assert step.criteria_config == [mock_criterion_config]
    assert step.significance_levels == [0.05, 0.01]
    assert step.monte_carlo_count == 42
    assert step.result_storage is storage
    assert step.results_path == results_path
    assert step.with_chart is ReportMode.WITHOUT_CHART


# Checks that sample sizes are sorted during initialization.
@pytest.mark.parametrize(("sample_sizes", "expected_sizes"), SAMPLE_SIZE_CASES)
def test_init_sorts_sample_sizes(step_factory, sample_sizes: list[int], expected_sizes: list[int]) -> None:
    assert step_factory(sample_sizes=sample_sizes).sizes == expected_sizes


# Checks that run builds the report with the collected critical values.
def test_run_builds_report_with_critical_values(step_factory, storage, builder, calculator) -> None:
    storage.get_data.return_value = make_limit_distribution()
    step = step_factory(significance_levels=[0.05, 0.01], sample_sizes=[10, 20])

    step.run()

    builder.assert_called_once_with(
        report_name="cv",
        criteria_config=step.criteria_config,
        sample_sizes=[10, 20],
        significance_levels=[0.05, 0.01],
        cv_values=[0.05, 0.01, 0.05, 0.01],
        results_path=step.results_path,
        with_chart=ReportMode.WITH_CHART,
    )
    builder.return_value.build.assert_called_once_with()


# Checks that one critical value is calculated per criterion, size and level combination.
@pytest.mark.parametrize(
    ("criteria_count", "sizes_count", "levels_count"),
    [(1, 1, 1), (2, 2, 3)],
)
def test_run_calculates_every_combination(
    step_factory, storage, builder, calculator, criteria_count: int, sizes_count: int, levels_count: int
) -> None:
    storage.get_data.return_value = make_limit_distribution()
    criteria = [
        MagicMock(criterion_code=f"CRIT_{index}_", criterion=MagicMock(parameters=[]))
        for index in range(criteria_count)
    ]
    step = step_factory(
        criteria_config=criteria,
        sample_sizes=[10 * (index + 1) for index in range(sizes_count)],
        significance_levels=[0.05 * (index + 1) for index in range(levels_count)],
    )

    step.run()

    assert calculator.return_value.calculate.call_count == criteria_count * sizes_count * levels_count
    assert storage.get_data.call_count == criteria_count * sizes_count
    assert len(builder.call_args.kwargs["cv_values"]) == criteria_count * sizes_count * levels_count


# Checks that the limit distribution is read with a query built from the step configuration.
@pytest.mark.parametrize("sample_size", [10, 20, 100])
def test_get_limit_distribution_builds_query(step_factory, storage, mock_criterion_config, sample_size: int) -> None:
    storage.get_data.return_value = make_limit_distribution(sample_size=sample_size)

    result = CriticalValueReportBuildingStep._get_limit_distribution_from_storage(
        storage=storage,
        criterion_config=mock_criterion_config,
        sample_size=sample_size,
        monte_carlo_count=7,
    )

    storage.get_data.assert_called_once_with(
        LimitDistributionQuery(
            criterion_code="KS_",
            criterion_parameters=[],
            sample_size=sample_size,
            monte_carlo_count=7,
        )
    )
    assert result == [0.1, 0.2, 0.3]


# Checks that a missing limit distribution raises a ValueError mentioning the query.
def test_get_limit_distribution_raises_when_missing(step_factory, storage, mock_criterion_config) -> None:
    storage.get_data.return_value = None

    with pytest.raises(ValueError, match="Limit distribution for query"):
        CriticalValueReportBuildingStep._get_limit_distribution_from_storage(
            storage=storage,
            criterion_config=mock_criterion_config,
            sample_size=10,
            monte_carlo_count=100,
        )
