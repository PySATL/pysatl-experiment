"""
Critical value experiment factory.

This module contains the factory implementation responsible for
constructing all experiment steps required for critical value
estimation.
"""

from typing_extensions import override

from pysatl_experiment.configuration import CriticalValueExperimentConfig
from pysatl_experiment.experiment_execution.experiment_factory.standard_generation_experiment_factory import (
    StandardGenerationExperimentFactory,
)
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.context import (
    CriticalValueExecutionContext,
)
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.critical_value_execution_step import (
    CriticalValueExecutionStep,
)
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.task_spec import CriticalValueTask
from pysatl_experiment.experiment_execution.step.report_step import ReportBuildingStep, ReportStepContext
from pysatl_experiment.experiment_execution.step.report_step.critical_value.critical_value_report_builder import (
    CriticalValueReportBuilder,
)
from pysatl_experiment.persistence.contracts.limit_distribution import ILimitDistributionStorage
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.query_results import QueryResults
from pysatl_experiment.persistence.sqlalchemy.limit_distribution import AlchemyLimitDistributionStorage
from pysatl_experiment.sample_loading.sqlalchemy_source import SqlAlchemySampleSourceFactory
from pysatl_experiment.utils.report_utils import get_report_template_dir


class CriticalValueExperimentFactory(
    StandardGenerationExperimentFactory[
        CriticalValueExperimentConfig,
        CriticalValueExecutionStep,
        ReportBuildingStep,
        ILimitDistributionStorage,
        CriticalValueTask,
    ]
):
    """
    Factory for critical value experiments.

    Creates generation, execution and report-building steps required
    for Monte Carlo estimation of critical values for statistical
    criteria.
    """

    def _create_execution_step(
        self,
        random_values_storage: IRandomValuesStorage,
        result_storage: ILimitDistributionStorage,
        step_config: list[CriticalValueTask],
    ) -> CriticalValueExecutionStep:
        """Assemble an execution step from the prepared tasks and dependencies."""
        return CriticalValueExecutionStep(
            context=CriticalValueExecutionContext(
                experiment_name=self.config.experiment_name,
                parallel_workers=self.config.execute.parallel_workers,
                tasks=tuple(step_config),
                write_batch_size=self.config.execute.write_batch_size,
            ),
            sample_source=SqlAlchemySampleSourceFactory(self.config.storage_connection),
            result_storage=result_storage,
        )

    def _create_report_building_step(self, result_storage: ILimitDistributionStorage) -> ReportBuildingStep:
        """Assemble the shared report step with a selected source and concrete builder."""
        context = ReportStepContext(
            report_name=self.config.experiment_name,
            template_path=get_report_template_dir() / "cv_template.html",
            results_path=self.config.report.results_path,
            report_mode=self.config.report.report_mode,
        )
        results = QueryResults(result_storage, self.config_adapter.result_queries())
        builder = CriticalValueReportBuilder(
            criteria_config=self.config_adapter.criteria_config(),
            sample_sizes=self.config_adapter.sample_sizes,
            significance_levels=self.config.execute.significance_levels,
        )
        return ReportBuildingStep(context=context, result_storage=results, report_builder=builder)

    @override
    def _init_result_storage(self) -> AlchemyLimitDistributionStorage:
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
        limit_distribution_storage = AlchemyLimitDistributionStorage(storage_connection)
        limit_distribution_storage.init()
        return limit_distribution_storage
