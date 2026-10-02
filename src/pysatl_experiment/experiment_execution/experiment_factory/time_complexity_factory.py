"""
Time complexity experiment factory.

This module contains the factory implementation responsible for
constructing experiment steps required to evaluate computational
complexity of statistical criteria.
"""

from typing_extensions import override

from pysatl_experiment.configuration import TimeComplexityExperimentConfig
from pysatl_experiment.experiment_execution.experiment_factory.standard_generation_experiment_factory import (
    StandardGenerationExperimentFactory,
)
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.context import (
    TimeComplexityExecutionContext,
)
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.task_spec import TimeComplexityTask
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.time_complexity_execution_step import (
    TimeComplexityExecutionStep,
)
from pysatl_experiment.experiment_execution.step.report_step import ReportBuildingStep, ReportStepContext
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder import (
    TimeComplexityReportBuilder,
)
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.contracts.time_complexity import ITimeComplexityStorage
from pysatl_experiment.persistence.sqlalchemy.time_complexity import AlchemyTimeComplexityStorage
from pysatl_experiment.persistence.time_complexity_results import TimeComplexityResults
from pysatl_experiment.sample_loading.sqlalchemy_source import SqlAlchemySampleSourceFactory
from pysatl_experiment.utils.report_utils import get_report_template_dir


class TimeComplexityExperimentFactory(
    StandardGenerationExperimentFactory[
        TimeComplexityExperimentConfig,
        TimeComplexityExecutionStep,
        ReportBuildingStep,
        ITimeComplexityStorage,
        TimeComplexityTask,
    ]
):
    """
    Factory for time complexity experiments.

    Creates generation, execution and report-building steps required
    for measuring execution time of statistical criteria for different
    sample sizes.
    """

    @override
    def _create_execution_step(
        self,
        data_storage: IRandomValuesStorage,
        result_storage: ITimeComplexityStorage,
        step_config: list[TimeComplexityTask],
    ) -> TimeComplexityExecutionStep:
        """Assemble an execution step from the prepared tasks and dependencies."""
        return TimeComplexityExecutionStep(
            context=TimeComplexityExecutionContext(
                experiment_name=self.config.experiment_name,
                parallel_workers=self.config.execute.parallel_workers,
                tasks=tuple(step_config),
                write_batch_size=self.config.execute.write_batch_size,
            ),
            sample_source=SqlAlchemySampleSourceFactory(self.config.storage_connection),
            result_storage=result_storage,
        )

    @override
    def _create_report_building_step(self, result_storage: ITimeComplexityStorage) -> ReportBuildingStep:
        """Assemble the shared report step with a selected source and concrete builder."""
        context = ReportStepContext(
            report_name=self.config.experiment_name,
            template_path=get_report_template_dir() / "tc_template.html",
            results_path=self.config.report.results_path,
            report_mode=self.config.report.report_mode,
        )
        results = TimeComplexityResults(
            result_storage, self.config.experiment_name, self.config_adapter.result_queries()
        )
        builder = TimeComplexityReportBuilder()
        return ReportBuildingStep(context=context, result_storage=results, report_builder=builder)

    @override
    def _init_result_storage(self) -> AlchemyTimeComplexityStorage:
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
        time_complexity_storage = AlchemyTimeComplexityStorage(storage_connection)
        time_complexity_storage.init()
        return time_complexity_storage
