"""Time complexity experiment execution step implementation."""

from dataclasses import dataclass

from typing_extensions import override

from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.configuration.models.parameters import NumericParameters
from pysatl_experiment.experiment_execution.parallel.task_spec import TaskSpec
from pysatl_experiment.experiment_execution.step.execution_step.execution_step_data import (
    ExecutionStepData,
    HypothesisGeneratorData,
)
from pysatl_experiment.experiment_execution.step.execution_step.multithreading_execution_step import (
    ExecutionTaskResult,
    MultithreadingExecutionStep,
)
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.time_complexity_worker import (
    TimeComplexityWorker,
    TimeComplexityWorkerResult,
)
from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.models.time_complexity import ITimeComplexityStorage, TimeComplexityModel


@dataclass
class TimeComplexityStepData(ExecutionStepData):
    """Data for a single execution step in time complexity experiment."""

    criterion_parameters: NumericParameters


TimeComplexityExecutionResult = ExecutionTaskResult[TimeComplexityWorkerResult]


class TimeComplexityExecutionStep(
    MultithreadingExecutionStep[
        TimeComplexityStepData,
        TimeComplexityExecutionResult,
        TimeComplexityModel,
        ITimeComplexityStorage,
    ]
):
    """
    Standard time complexity experiment execution step.

    The step measures criterion execution time for different sample sizes.
    """

    def __init__(
        self,
        experiment_id: int,
        experiment_name: str,
        hypothesis_generator_data: HypothesisGeneratorData,
        step_config: list[TimeComplexityStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
        result_storage: ITimeComplexityStorage,
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
        self.hypothesis_generator_data = hypothesis_generator_data
        self.data_storage = data_storage

    @override
    def _collect_tasks(self) -> list[TaskSpec]:
        task_specs = []
        for step_data in self.step_config:
            spec = TaskSpec(
                experiment_type=ExperimentType.TIME_COMPLEXITY,
                experiment_name=self.experiment_name,
                statistic_class_name=step_data.statistics.__class__.__name__,
                statistic_module=step_data.statistics.__class__.__module__,
                criterion_code=step_data.statistics.code(),
                criterion_parameters=step_data.criterion_parameters,
                sample_size=step_data.sample_size,
                monte_carlo_count=self.monte_carlo_count,
                db_path=self.storage_connection,
                sample_generator_code=self.hypothesis_generator_data.generator_code,
                sample_generator_parameters=self.hypothesis_generator_data.parameters,
                hypothesis_generator=self.hypothesis_generator_data.generator_code,
                hypothesis_parameters=self.hypothesis_generator_data.parameters,
            )
            task_specs.append(spec)
        return task_specs

    @staticmethod
    @override
    def _execute_task(spec: TaskSpec) -> TimeComplexityExecutionResult:
        sample_data, statistics = TimeComplexityExecutionStep._load_samples_and_statistics(spec)
        worker = TimeComplexityWorker(statistics=statistics, sample_data=sample_data)
        return ExecutionTaskResult(spec=spec, worker_result=worker.execute())

    @override
    def _to_model(self, result: TimeComplexityExecutionResult) -> TimeComplexityModel:
        spec = result.spec
        return TimeComplexityModel(
            experiment_name=self.experiment_name,
            criterion_code=spec.criterion_code,
            criterion_parameters=spec.criterion_parameters,
            sample_size=spec.sample_size,
            samples_count=spec.monte_carlo_count,
            results_times=result.worker_result.results_times,
        )

    @override
    def _bulk_save(self, models: list[TimeComplexityModel]) -> None:
        self.result_storage.bulk_insert_data(models)
