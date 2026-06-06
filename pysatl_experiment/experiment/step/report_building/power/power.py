"""Power report building step implementation."""

from pathlib import Path

from line_profiler import profile
from typing_extensions import override

from pysatl_experiment.configuration.criteria_config.criteria_config import CriterionConfig
from pysatl_experiment.configuration.model.alternative.alternative import Alternative
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.experiment.model.experiment_step.experiment_step import IExperimentStep
from pysatl_experiment.persistence.model.power.power import IPowerStorage, PowerQuery
from pysatl_experiment.report.power.power import PowerReportBuilder


class PowerReportBuildingStep(IExperimentStep):
    """Standard power experiment report building step."""

    def __init__(
        self,
        report_name: str,
        criteria_config: list[CriterionConfig],
        significance_levels: list[float],
        alternatives: list[Alternative],
        sample_sizes: list[int],
        monte_carlo_count: int,
        result_storage: IPowerStorage,
        results_path: Path,
        with_chart: ReportMode,
    ) -> None:
        """
        Initialize power report building step.

        Parameters
        ----------
        report_name : str
            Name of the generated report.
        criteria_config : list[CriterionConfig]
            Statistical criteria configurations.
        significance_levels : list[float]
            Significance levels.
        alternatives : list[Alternative]
            Alternative distribution configurations.
        sample_sizes : list[int]
            Sample sizes used in experiments.
        monte_carlo_count : int
            Number of Monte Carlo iterations.
        result_storage : IPowerStorage
            Storage with power experiment results.
        results_path : Path
            Output directory for generated reports.
        with_chart : ReportMode
            Report visualization mode.
        """
        self.report_name = report_name
        self.criteria_config = criteria_config
        self.significance_levels = significance_levels
        self.alternatives = alternatives
        self.sizes = sorted(sample_sizes)
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path
        self.with_chart = with_chart

    @profile
    @override
    def run(self) -> None:
        """Collect power statistics and build report."""
        power_data = self._collect_statistics()

        builder = PowerReportBuilder(
            report_name=self.report_name,
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
        Collect power experiment results from storage.

        Returns
        -------
        dict[str, dict[tuple[str, float], dict[int, list[bool]]]]
            Nested mapping of criterion results grouped by
            alternative distribution, significance level,
            and sample size.
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
        Load power experiment result from storage.

        Parameters
        ----------
        criterion_config : CriterionConfig
            Criterion configuration.
        sample_size : int
            Sample size.
        alternative : Alternative
            Alternative distribution configuration.
        significance_level : float
            Significance level.

        Returns
        -------
        list[bool]
            Criterion decisions.

        Raises
        ------
        ValueError
            If results are not found.
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
