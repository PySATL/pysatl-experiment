from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic

from stattest.experiment.generator import AbstractRVSGenerator
from stattest.persistence.model.power.power import IPowerStorage
from stattest.report.power.power import PowerReportBuilder


class PowerReportBuildingStep:
    """
    Standard power experiment report building step.
    """

    def __init__(
        self,
        criteria: list[AbstractGoodnessOfFitStatistic],
        significance_levels: list[float],
        alternatives: list[AbstractRVSGenerator],
        sizes: list[int],
        monte_carlo_count: int,
        report_builder: PowerReportBuilder,
        result_storage: IPowerStorage,
    ):
        self.criteria = criteria
        self.significance_levels = significance_levels
        self.alternatives = alternatives
        self.sizes = sizes
        self.monte_carlo_count = monte_carlo_count
        self.report_builder = report_builder
        self.result_storage = result_storage

    def run(self) -> None:
        """
        Run standard power report building step.
        """
        raise NotImplementedError("Method is not yet implemented")
