"""Power experiment execution step implementation."""

from dataclasses import dataclass

from typing_extensions import override

from pysatl_experiment.configuration.models.alternative import Alternative
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.experiment_execution.parallel.task_spec import TaskSpec
from pysatl_experiment.experiment_execution.step.execution_step.execution_step_data import ExecutionStepData
from pysatl_experiment.experiment_execution.step.execution_step.multithreading_execution_step import (
    ExecutionTaskResult,
    MultithreadingExecutionStep,
)
from pysatl_experiment.experiment_execution.step.execution_step.power.power_worker import PowerWorker, PowerWorkerResult
from pysatl_experiment.persistence.models.power import IPowerStorage, PowerModel
from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage


@dataclass
class PowerStepData(ExecutionStepData):
    """
    Data for a single execution step in power experiment.

    Attributes
    ----------
    alternative : Alternative
        Alternative distribution configuration.
    significance_level : float
        Significance level used for the criterion.
    """

    alternative: Alternative
    significance_level: float


PowerExecutionResult = ExecutionTaskResult[PowerWorkerResult]


class PowerExecutionStep(MultithreadingExecutionStep[PowerStepData, PowerExecutionResult, PowerModel, IPowerStorage]):
    """
    Standard power experiment execution step.

    The step evaluates statistical power for multiple
    alternatives and significance levels.
    """

    def __init__(
        self,
        experiment_id: int,
        experiment_name: str,
        step_config: list[PowerStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
        result_storage: IPowerStorage,
        storage_connection: str,
        parallel_workers: int,
    ) -> None:
        super().__init__(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            step_config=step_config,
            monte_carlo_count=monte_carlo_count,
            result_storage=result_storage,
            storage_connection=storage_connection,
            parallel_workers=parallel_workers,
        )
        self.data_storage = data_storage

    @override
    def _collect_tasks(self) -> list[TaskSpec]:
        task_specs = []
        for step_data in self.step_config:
            alternative = step_data.alternative
            spec = TaskSpec(
                experiment_type=ExperimentType.POWER,
                experiment_name=self.experiment_name,
                statistic_class_name=step_data.statistics.__class__.__name__,
                statistic_module=step_data.statistics.__class__.__module__,
                criterion_code=step_data.statistics.code(),
                criterion_parameters=step_data.criterion_parameters,
                sample_size=step_data.sample_size,
                monte_carlo_count=self.monte_carlo_count,
                db_path=self.storage_connection,
                sample_generator_code=alternative.distribution_type,
                sample_generator_parameters=alternative.parameters,
                alternative_generator=alternative.distribution_type,
                alternative_parameters=alternative.parameters,
                significance_level=step_data.significance_level,
            )
            task_specs.append(spec)
        return task_specs

    @staticmethod
    @override
    def _execute_task(spec: TaskSpec) -> PowerExecutionResult:
        sample_data, statistics = PowerExecutionStep._load_samples_and_statistics(spec)
        if spec.significance_level is None:
            raise ValueError("Significance level is required for power experiment.")

        worker = PowerWorker(
            statistics=statistics,
            sample_data=sample_data,
            significance_level=spec.significance_level,
            storage_connection=spec.db_path,
        )
        return ExecutionTaskResult(spec=spec, worker_result=worker.execute())

    @override
    def _to_model(self, result: PowerExecutionResult) -> PowerModel:
        spec = result.spec
        if spec.significance_level is None:
            raise ValueError("significance_level is required for power tasks")
        return PowerModel(
            experiment_id=self.experiment_id,
            criterion_code=spec.criterion_code,
            criterion_parameters=spec.criterion_parameters,
            sample_size=spec.sample_size,
            alternative_code=spec.alternative_generator,
            alternative_parameters=spec.alternative_parameters,
            monte_carlo_count=spec.monte_carlo_count,
            significance_level=float(spec.significance_level),
            results_criteria=result.worker_result.results_criteria,
        )

    @override
    def _bulk_save(self, models: list[PowerModel]) -> None:
        self.result_storage.bulk_insert_data(models)
