from pathlib import Path

from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.configuration.model.alternative.alternative import Alternative
from stattest.persistence.model.power.power import IPowerStorage, PowerQuery
from stattest.report.power.power import PowerReportBuilder


class PowerReportBuildingStep:
    """
    Standard power experiment report building step.
    """

    def __init__(
        self,
        criteria_config: list[CriterionConfig],
        significance_levels: list[float],
        alternatives: list[Alternative],
        sample_sizes: list[int],
        monte_carlo_count: int,
        result_storage: IPowerStorage,
        results_path: Path,
    ):
        self.criteria_config = criteria_config
        self.significance_levels = significance_levels
        self.alternatives = alternatives
        self.sizes = sample_sizes
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path

    def run(self) -> None:
        """
        Run standard power report building step.
        """

        for criterion_config in self.criteria_config:
            for alternative in self.alternatives:
                for sample_size in self.sizes:
                    for significance_level in self.significance_levels:
                        results_criteria = self._get_power_result_from_storage(
                            criterion_config=criterion_config,
                            sample_size=sample_size,
                            alternative=alternative,
                            significance_level=significance_level,
                        )

                        report_builder = PowerReportBuilder(
                            criterion_config=criterion_config,
                            sample_size=sample_size,
                            alternative=alternative,
                            significance_level=significance_level,
                            power_result=results_criteria,
                            results_path=self.results_path,
                        )
                        report_builder.build()

    def _get_power_result_from_storage(
        self,
        criterion_config: CriterionConfig,
        sample_size: int,
        alternative: Alternative,
        significance_level: float,
    ) -> list[bool]:
        """
        Get limit distribution from storage.

        :param criterion_config: criterion configuration.
        :param sample_size: sample size.
        :param alternative: alternative.
        :param significance_level: significance level.

        :return: limit distribution.
        """

        query = PowerQuery(
            criterion_code=criterion_config.criterion_code,
            criterion_parameters=criterion_config.criterion.parameters,
            sample_size=sample_size,
            alternative_code=alternative.generator_name,
            alternative_parameters=alternative.parameters,
            monte_carlo_count=self.monte_carlo_count,
            significance_level=significance_level,
        )

        storage = self.result_storage

        result = storage.get_data(query)
        if result is None:
            raise ValueError(f"Power for query {query} not found.")

        results_criteria = result.results_criteria

        return results_criteria
