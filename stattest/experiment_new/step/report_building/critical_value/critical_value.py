from pathlib import Path

from pysatl_criterion.persistence.model.limit_distribution.limit_distribution import (
    ILimitDistributionStorage,
    LimitDistributionQuery,
)
from stattest.configuration.criteria_config.criteria_config import CriterionConfig
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
    ):
        self.criteria_config = criteria_config
        self.significance_levels = significance_levels
        self.sizes = sample_sizes
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path

    def run(self) -> None:
        """
        Run standard critical value report building step.
        """

        for criterion_config in self.criteria_config:
            for sample_size in self.sizes:
                limit_distribution = self._get_limit_distribution_from_storage(
                    storage=self.result_storage,
                    criterion_config=criterion_config,
                    sample_size=sample_size,
                    monte_carlo_count=self.monte_carlo_count,
                )
                for significance_level in self.significance_levels:
                    report_builder = CriticalValueReportBuilder(
                        criterion_config=criterion_config,
                        sample_size=sample_size,
                        significance_level=significance_level,
                        limit_distribution=limit_distribution,
                        results_path=self.results_path,
                    )
                    report_builder.build()

    def _get_limit_distribution_from_storage(
        self,
        storage: ILimitDistributionStorage,
        criterion_config: CriterionConfig,
        sample_size: int,
        monte_carlo_count: int,
    ) -> list[float]:
        """
        Get limit distribution from storage.

        :param storage: storage.
        :param criterion_config: criterion configuration.
        :param sample_size: sample size.
        :param monte_carlo_count: monte carlo count.

        :return: limit distribution.
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
