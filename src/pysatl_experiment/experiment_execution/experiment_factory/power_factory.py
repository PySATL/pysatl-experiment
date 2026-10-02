"""
Power experiment factory.

This module contains the factory implementation responsible for
constructing experiment steps required to estimate statistical power
for goodness-of-fit criteria under alternative distributions.
"""

from typing_extensions import override

from pysatl_experiment.configuration import PowerExperimentConfig
from pysatl_experiment.experiment_execution.experiment_factory.standard_generation_experiment_factory import (
    StandardGenerationExperimentFactory,
)
from pysatl_experiment.experiment_execution.step.execution_step.power.context import PowerExecutionContext
from pysatl_experiment.experiment_execution.step.execution_step.power.power_execution_step import (
    PowerExecutionStep,
)
from pysatl_experiment.experiment_execution.step.execution_step.power.task_spec import PowerTask
from pysatl_experiment.experiment_execution.step.report_step import ReportBuildingStep, ReportStepContext
from pysatl_experiment.experiment_execution.step.report_step.power.power_report_builder import PowerReportBuilder
from pysatl_experiment.persistence.contracts.power import IPowerStorage
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.query_results import QueryResults
from pysatl_experiment.persistence.sqlalchemy.power import AlchemyPowerStorage
from pysatl_experiment.sample_loading.sqlalchemy_source import SqlAlchemySampleSourceFactory
from pysatl_experiment.utils.report_utils import get_report_template_dir


class PowerExperimentFactory(
    StandardGenerationExperimentFactory[
        PowerExperimentConfig,
        PowerExecutionStep,
        ReportBuildingStep,
        IPowerStorage,
        PowerTask,
    ]
):
    """
    Factory for statistical power experiments.

    Creates generation, execution and report-building steps required
    for statistical power estimation under configured alternative
    distributions.
    """

    def _create_execution_step(
        self,
        data_storage: IRandomValuesStorage,
        result_storage: IPowerStorage,
        step_config: list[PowerTask],
    ) -> PowerExecutionStep:
        """Assemble an execution step from the prepared tasks and dependencies."""
        return PowerExecutionStep(
            context=PowerExecutionContext(
                experiment_name=self.config.experiment_name,
                parallel_workers=self.config.execute.parallel_workers,
                tasks=tuple(step_config),
                write_batch_size=self.config.execute.write_batch_size,
            ),
            sample_source=SqlAlchemySampleSourceFactory(self.config.storage_connection),
            result_storage=result_storage,
            storage_connection=self.config.storage_connection,
        )

    def _create_report_building_step(self, result_storage: IPowerStorage) -> ReportBuildingStep:
        """Assemble the shared report step with a selected source and concrete builder."""
        context = ReportStepContext(
            report_name=self.config.experiment_name,
            template_path=get_report_template_dir() / "power_template.html",
            results_path=self.config.report.results_path,
            report_mode=self.config.report.report_mode,
        )
        results = QueryResults(result_storage, self.config_adapter.result_queries())
        builder = PowerReportBuilder(
            criteria_config=self.config_adapter.criteria_config(),
            sample_sizes=self.config_adapter.sample_sizes,
            significance_levels=self.config.execute.significance_levels,
            alternatives=self.config_adapter.alternatives,
        )
        return ReportBuildingStep(context=context, result_storage=results, report_builder=builder)

    @override
    def _init_result_storage(self) -> AlchemyPowerStorage:
        """
        Initialize result storage.

        Creates and initializes a storage implementation corresponding
        to the configured experiment type.

        Returns
        -------
        RS
            Initialized result storage.

        Raises
        ------
        ValueError
            If the experiment type is unsupported.
        """
        storage_connection = self.config.storage_connection
        power_storage = AlchemyPowerStorage(storage_connection)
        power_storage.init()
        return power_storage
