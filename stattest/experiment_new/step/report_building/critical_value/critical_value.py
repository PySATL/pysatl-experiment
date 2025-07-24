from pathlib import Path

from pysatl_criterion.cv_calculator.cv_calculator.cv_calculator import CVCalculator
from pysatl_criterion.persistence.model.limit_distribution.limit_distribution import (
    ILimitDistributionStorage, LimitDistributionQuery,
)

from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.configuration.model.report_mode.report_mode import ReportMode
from stattest.report.critical_value.critical_value import CriticalValueReportBuilder


class CriticalValueReportBuildingStep:
    """
    Standard critical value experiment report building step.
    """

    def __init__(
            self,
            criteria_config: list[CriterionConfig],
            significance_levels: list[float],
            sample_sizes: list[int],
            monte_carlo_count: int,
            result_storage: ILimitDistributionStorage,
            results_path: Path,
            with_chart: ReportMode,
    ):
        self.criteria_config = criteria_config
        self.significance_levels = significance_levels
        self.sizes = sorted(sample_sizes)
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path
        self.with_chart = with_chart

    def run(self) -> None:
        """
        Run standard critical value report building step.
        """

        cv_values = []
        for criterion_config in self.criteria_config:
            for sample_size in self.sizes:
                cv_calculator = CVCalculator(self.result_storage)
                for significance_level in self.significance_levels:
                    cv_value = cv_calculator.calculate_critical_value(criterion_config.criterion_code, sample_size,
                                                                      significance_level)

                    cv_values.append(cv_value)

        report_builder = CriticalValueReportBuilder(
            criteria_config=self.criteria_config,
            sample_sizes=self.sizes,
            significance_levels=self.significance_levels,
            cv_values=cv_values,
            results_path=self.results_path,
            with_chart=self.with_chart,
        )
        report_builder.build()

    def _get_limit_distribution_from_storage(
            self,
            storage: ILimitDistributionStorage,
            criterion_config: CriterionConfig,
            sample_size: int,
            monte_carlo_count: int,
    ) -> list[float]:

        """Get limit distribution from storage.

        :param storage: storage.
        :param criterion_config: criterion configuration.
        :param sample_size: sample size.
        :param monte_carlo_count: monte carlo count.

        :return: limit distribution."""

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
