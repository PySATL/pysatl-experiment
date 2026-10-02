"""Execute prepared critical value tasks with separately supplied storage dependencies."""

from functools import partial

from typing_extensions import override

from pysatl_experiment.experiment_execution.step.execution_step.parallel_execution_step import (
    ExecutionTaskResult,
    ParallelExecutionStep,
)
from pysatl_experiment.persistence.contracts.limit_distribution import ILimitDistributionStorage
from pysatl_experiment.persistence.models.limit_distribution import LimitDistributionModel
from pysatl_experiment.sample_loading.source import SampleSource, SampleSourceFactory

from .context import CriticalValueExecutionContext
from .critical_value_worker import CriticalValueWorker, CriticalValueWorkerResult
from .task_spec import CriticalValueTask


CriticalValueExecutionResult = ExecutionTaskResult[CriticalValueTask, CriticalValueWorkerResult]


class CriticalValueExecutionStep(
    ParallelExecutionStep[
        CriticalValueTask, CriticalValueExecutionResult, LimitDistributionModel, ILimitDistributionStorage, SampleSource
    ]
):
    """Load and compute in child processes; save results in the parent process."""

    def __init__(
        self,
        context: CriticalValueExecutionContext,
        sample_source: SampleSourceFactory,
        result_storage: ILimitDistributionStorage,
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
    def _collect_tasks(self) -> list[CriticalValueTask]:
        return list(self.context.tasks)

    @override
    def _make_task(self, spec: CriticalValueTask):
        return partial(type(self)._execute_task, spec)

    @staticmethod
    def _execute_task(spec: CriticalValueTask, source: SampleSource) -> CriticalValueExecutionResult:
        """Load samples and construct the configured statistic in the worker process."""
        samples = source.load(spec.sample_set)
        statistics = spec.criterion.implementation(**spec.criterion.parameters)
        worker = CriticalValueWorker(statistics=statistics, sample_data=samples)
        return ExecutionTaskResult(spec=spec, worker_result=worker.execute())

    @override
    def _to_model(self, result: CriticalValueExecutionResult) -> LimitDistributionModel:
        spec = result.spec
        return LimitDistributionModel(
            experiment_name=spec.sample_set.experiment_name,
            criterion_code=spec.criterion.code,
            criterion_parameters=spec.criterion.parameters,
            sample_size=spec.sample_set.sample_size,
            monte_carlo_count=spec.sample_set.samples_count,
            results_statistics=result.worker_result.results_statistics,
        )

    @override
    def _bulk_save(self, models: list[LimitDistributionModel]) -> None:
        self.result_storage.bulk_insert_data(models)
