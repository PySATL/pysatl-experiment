from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic

from stattest.persistence.model.time_complexity.time_complexity import ITimeComplexityStorage
from stattest.report.time_complexity.time_complexity import TimeComplexityReportBuilder


class TimeComplexityReportBuildingStep:
    """
    Standard time complexity experiment report building step.
    """

    def __init__(
        self,
        criteria: list[AbstractGoodnessOfFitStatistic],
        sizes: list[int],
        monte_carlo_count: int,
        report_builder: TimeComplexityReportBuilder,
        result_storage: ITimeComplexityStorage,
        results_path: str,
    ):
        self.criteria = criteria
        self.sizes = sizes
        self.monte_carlo_count = monte_carlo_count
        self.report_builder = report_builder
        self.result_storage = result_storage
        self.results_path = results_path

    def run(self) -> None:
        """
        Run standard time complexity report building step.
        """
        raise NotImplementedError("Method is not yet implemented")
