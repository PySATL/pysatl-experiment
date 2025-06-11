from pathlib import Path

from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityQuery,
)
from stattest.report.time_complexity.time_complexity import TimeComplexityReportBuilder


class TimeComplexityReportBuildingStep:
    """
    Standard time complexity experiment report building step.
    """

    def __init__(
        self,
        criteria_config: list[CriterionConfig],
        sample_sizes: list[int],
        monte_carlo_count: int,
        result_storage: ITimeComplexityStorage,
        results_path: Path,
    ):
        self.criteria_config = criteria_config
        self.sizes = sample_sizes
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path

    def run(self) -> None:
        """
        Run standard time complexity report building step.
        """

        for criterion_config in self.criteria_config:
            for sample_size in self.sizes:
                times = self._get_times_from_storage(
                    storage=self.result_storage,
                    criterion_config=criterion_config,
                    sample_size=sample_size,
                    monte_carlo_count=self.monte_carlo_count,
                )
                report_builder = TimeComplexityReportBuilder(
                    criterion_config=criterion_config,
                    sample_size=sample_size,
                    times=times,
                    results_path=self.results_path,
                )
                report_builder.build()

    def _get_times_from_storage(
        self,
        storage: ITimeComplexityStorage,
        criterion_config: CriterionConfig,
        sample_size: int,
        monte_carlo_count: int,
    ) -> list[float]:
        """
        Get times from time complexity storage.

        :param storage: storage.
        :param criterion_config: criterion configuration.
        :param sample_size: sample size.
        :param monte_carlo_count: monte carlo count.

        :return: times.
        """

        query = TimeComplexityQuery(
            criterion_code=criterion_config.criterion_code,
            criterion_parameters=criterion_config.criterion.parameters,
            sample_size=sample_size,
            monte_carlo_count=monte_carlo_count,
        )

        result = storage.get_data(query)
        if result is None:
            raise ValueError(f"Times for query {query} not found.")

        times = result.results_times

        return times
