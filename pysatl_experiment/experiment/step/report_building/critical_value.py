"""Critical value report building step implementation."""

from pathlib import Path

from line_profiler import profile
from pysatl_criterion.hypothesis_testing.critical_values.cv_calculator.cv_calculator import CVCalculator
from pysatl_criterion.persistence.models.limit_distribution import ILimitDistributionStorage, LimitDistributionQuery
from typing_extensions import override

from pysatl_experiment.configuration.criteria_config import CriterionConfig
from pysatl_experiment.configuration.model.report_mode import ReportMode
from pysatl_experiment.experiment.model.experiment_step import IExperimentStep
from pysatl_experiment.report.critical_value import CriticalValueReportBuilder


class CriticalValueReportBuildingStep(IExperimentStep):
    """Standard critical value experiment report building step."""

    def __init__(
        self,
        report_name: str,
        criteria_config: list[CriterionConfig],
        significance_levels: list[float],
        sample_sizes: list[int],
        monte_carlo_count: int,
        result_storage: ILimitDistributionStorage,
        results_path: Path,
        with_chart: ReportMode,
    ) -> None:
        """
        Initialize critical value report builder step.

        Parameters
        ----------
        report_name : str
            Name of the generated report.
        criteria_config : list[CriterionConfig]
            Statistical criteria configurations.
        significance_levels : list[float]
            Significance levels.
        sample_sizes : list[int]
            Sample sizes used in experiments.
        monte_carlo_count : int
            Number of Monte Carlo iterations.
        result_storage : ILimitDistributionStorage
            Storage with limit distributions.
        results_path : Path
            Output directory for generated reports.
        with_chart : ReportMode
            Report visualization mode.
        """
        self.criteria_config = criteria_config
        self.report_name = report_name
        self.significance_levels = significance_levels
        self.sizes = sorted(sample_sizes)
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path
        self.with_chart = with_chart

    @profile
    @override
    def run(self) -> None:
        """Calculate critical values and build report."""
        cv_values = []
        for criterion_config in self.criteria_config:
            for sample_size in self.sizes:
                cv_calculator = CVCalculator(self.result_storage)
                for significance_level in self.significance_levels:
                    cv_value = cv_calculator.calculate_critical_value(
                        criterion_config.criterion_code, sample_size, significance_level
                    )

                    cv_values.append(cv_value)

        report_builder = CriticalValueReportBuilder(
            report_name=self.report_name,
            criteria_config=self.criteria_config,
            sample_sizes=self.sizes,
            significance_levels=self.significance_levels,
            cv_values=cv_values,
            results_path=self.results_path,
            with_chart=self.with_chart,
        )
        report_builder.build()

    @staticmethod
    def _get_limit_distribution_from_storage(
        storage: ILimitDistributionStorage,
        criterion_config: CriterionConfig,
        sample_size: int,
        monte_carlo_count: int,
    ) -> list[float]:
        """
        Load empirical limit distribution from storage.

        Parameters
        ----------
        storage : ILimitDistributionStorage
            Limit distribution storage.
        criterion_config : CriterionConfig
            Criterion configuration.
        sample_size : int
            Sample size.
        monte_carlo_count : int
            Number of Monte Carlo iterations.

        Returns
        -------
        list[float]
            Empirical limit distribution.

        Raises
        ------
        ValueError
            If the distribution is not found.
        """
        query = LimitDistributionQuery(
            criterion_code=criterion_config.criterion_code,
            criterion_parameters=criterion_config.criterion.parameters,
            sample_size=sample_size,
            monte_carlo_count=monte_carlo_count,
        )

        result = storage.get_data(query)
        if result is None:
            raise ValueError(f"Limit distribution for query {query} not found.")

        limit_distribution = result.results_statistics

        return limit_distribution
