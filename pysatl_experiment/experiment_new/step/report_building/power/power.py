from pathlib import Path

from line_profiler import profile

from pysatl_experiment.configuration.criteria_config.criteria_config import CriterionConfig
from pysatl_experiment.configuration.model.alternative.alternative import Alternative
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.persistence.model.power.power import IPowerStorage, PowerQuery
from pysatl_experiment.report.power.power import PowerReportBuilder


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
        with_chart: ReportMode,
    ):
        self.criteria_config = criteria_config
        self.significance_levels = significance_levels
        self.alternatives = alternatives
        self.sizes = sorted(sample_sizes)
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path
        self.with_chart = with_chart

    @profile
    def run(self) -> None:
        """
        Run standard power report building step.
        """

        power_data = self._collect_statistics()

        builder = PowerReportBuilder(
            criteria_config=self.criteria_config,
            sample_sizes=self.sizes,
            alternatives=self.alternatives,
            significance_levels=self.significance_levels,
            power_result=power_data,
            results_path=self.results_path,
            with_chart=self.with_chart,
        )
        builder.build()

    def _collect_statistics(self) -> dict[str, dict[tuple[str, float], dict[int, list[bool]]]]:
        """
        Collect power results.

        :return: {criterion_code -> (alt_name, alpha) -> {size: [bool]}}
        """

        power_data: dict[str, dict[tuple[str, float], dict[int, list[bool]]]] = {}

        for criterion_config in self.criteria_config:
            for alternative in self.alternatives:
                for significance_level in self.significance_levels:
                    for sample_size in self.sizes:
                        result = self._get_power_result_from_storage(
                            criterion_config=criterion_config,
                            sample_size=sample_size,
                            alternative=alternative,
                            significance_level=significance_level,
                        )
                        key = (alternative.generator_name, significance_level)

                        level1_dict = power_data.setdefault(criterion_config.criterion_code, {})
                        level2_dict = level1_dict.setdefault(key, {})
                        level2_dict[sample_size] = result

        return power_data

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
