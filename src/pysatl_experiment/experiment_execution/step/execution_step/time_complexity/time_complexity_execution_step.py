"""Execute prepared time complexity tasks with separately supplied storage dependencies."""

from functools import partial

from typing_extensions import override

from pysatl_experiment.experiment_execution.step.execution_step.parallel_execution_step import (
    ExecutionTaskResult,
    ParallelExecutionStep,
)
from pysatl_experiment.persistence.contracts.time_complexity import ITimeComplexityStorage
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel
from pysatl_experiment.sample_loading.source import SampleSource, SampleSourceFactory

from .context import TimeComplexityExecutionContext
from .task_spec import TimeComplexityTask
from .time_complexity_worker import TimeComplexityWorker, TimeComplexityWorkerResult


TimeComplexityExecutionResult = ExecutionTaskResult[TimeComplexityTask, TimeComplexityWorkerResult]


class TimeComplexityExecutionStep(
    ParallelExecutionStep[
        TimeComplexityTask, TimeComplexityExecutionResult, TimeComplexityModel, ITimeComplexityStorage, SampleSource
    ]
):
    """Load and compute in child processes; save results in the parent process."""

    def __init__(
        self,
        context: TimeComplexityExecutionContext,
        sample_source: SampleSourceFactory,
        result_storage: ITimeComplexityStorage,
    ) -> None:
        super().__init__(
            parallel_workers=context.parallel_workers,
            result_storage=result_storage,
            context_factory=sample_source,
            total_tasks=len(context.tasks),
            write_batch_size=context.write_batch_size,
        )
        self.context = context

    @property
    def experiment_name(self) -> str:
        """Return the experiment identity owned by the context."""
        return self.context.experiment_name

    @override
    def _collect_tasks(self) -> list[TimeComplexityTask]:
        return list(self.context.tasks)

    @override
    def _make_task(self, spec: TimeComplexityTask):
        return partial(type(self)._execute_task, spec)

    @staticmethod
    def _execute_task(spec: TimeComplexityTask, source: SampleSource) -> TimeComplexityExecutionResult:
        """Reuse the worker sample source and construct the configured statistic before timing."""
        samples = source.load(spec.sample_set)
        statistics = spec.criterion.implementation(**spec.criterion.parameters)
        worker = TimeComplexityWorker(statistics=statistics, sample_data=samples)
        return ExecutionTaskResult(spec=spec, worker_result=worker.execute())

    @override
    def _to_model(self, result: TimeComplexityExecutionResult) -> TimeComplexityModel:
        spec = result.spec
        return TimeComplexityModel(
            experiment_name=spec.sample_set.experiment_name,
            generator_code=spec.sample_set.generator_code,
            criterion_code=spec.criterion.code,
            criterion_parameters=spec.criterion.parameters,
            sample_size=spec.sample_set.sample_size,
            samples_count=spec.sample_set.samples_count,
            results_times=result.worker_result.results_times,
        )

    @override
    def _bulk_save(self, models: list[TimeComplexityModel]) -> None:
        self.result_storage.bulk_insert(models, batch_size=self.write_batch_size)
