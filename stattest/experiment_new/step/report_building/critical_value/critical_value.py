from pysatl_criterion.persistence.model.limit_distribution.limit_distribution import (
    ILimitDistributionStorage,
)
from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic

from stattest.report.critical_value.critical_value import CriticalValueReportBuilder


class CriticalValueReportBuildingStep:
    """
    Standard critical value experiment report building step.
    """

    def __init__(
        self,
        criteria: list[AbstractGoodnessOfFitStatistic],
        significance_levels: list[float],
        sizes: list[int],
        monte_carlo_count: int,
        report_builder: CriticalValueReportBuilder,
        result_storage: ILimitDistributionStorage,
    ):
        self.criteria = criteria
        self.significance_levels = significance_levels
        self.sizes = sizes
        self.monte_carlo_count = monte_carlo_count
        self.report_builder = report_builder
        self.result_storage = result_storage

    def run(self) -> None:
        """
        Run standard critical value report building step.
        """
        pass
