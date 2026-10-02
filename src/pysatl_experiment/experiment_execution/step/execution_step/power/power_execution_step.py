"""Execute prepared power tasks with separately supplied storage dependencies."""

from functools import partial

from typing_extensions import override

from pysatl_experiment.experiment_execution.step.execution_step.parallel_execution_step import (
    ExecutionTaskResult,
    ParallelExecutionStep,
)
from pysatl_experiment.persistence.contracts.power import IPowerStorage
from pysatl_experiment.persistence.models.power import PowerModel
from pysatl_experiment.sample_loading.source import SampleSource, SampleSourceFactory

from .context import PowerExecutionContext
from .power_worker import PowerWorker, PowerWorkerResult
from .task_spec import PowerTask


PowerExecutionResult = ExecutionTaskResult[PowerTask, PowerWorkerResult]


class PowerExecutionStep(
    ParallelExecutionStep[PowerTask, PowerExecutionResult, PowerModel, IPowerStorage, SampleSource]
):
    """Load and compute in child processes; save results in the parent process."""

    def __init__(
        self,
        context: PowerExecutionContext,
        sample_source: SampleSourceFactory,
        result_storage: IPowerStorage,
        *,
        storage_connection: str,
    ) -> None:
        super().__init__(
            parallel_workers=context.parallel_workers,
            result_storage=result_storage,
            context_factory=sample_source,
            total_tasks=len(context.tasks),
            write_batch_size=context.write_batch_size,
        )
        self.context = context
        self.storage_connection = storage_connection

    @property
    def experiment_name(self) -> str:
        """Return the experiment identity owned by the context."""
        return self.context.experiment_name

    @override
    def _collect_tasks(self) -> list[PowerTask]:
        return list(self.context.tasks)

    @override
    def _make_task(self, spec: PowerTask):
        return partial(type(self)._execute_task, spec, storage_connection=self.storage_connection)

    @staticmethod
    def _execute_task(spec: PowerTask, source: SampleSource, *, storage_connection: str) -> PowerExecutionResult:
        """Load samples and construct the configured statistic in the worker process."""
        samples = source.load(spec.sample_set)
        statistics = spec.criterion.implementation(**spec.criterion.parameters)
        worker = PowerWorker(
            statistics=statistics,
            sample_data=samples,
            significance_level=spec.significance_level,
            storage_connection=storage_connection,
        )
        return ExecutionTaskResult(spec=spec, worker_result=worker.execute())

    @override
    def _to_model(self, result: PowerExecutionResult) -> PowerModel:
        spec = result.spec
        return PowerModel(
            experiment_name=spec.sample_set.experiment_name,
            alternative_code=spec.sample_set.generator_code,
            alternative_parameters=spec.alternative_parameters,
            significance_level=spec.significance_level,
            criterion_code=spec.criterion.code,
            criterion_parameters=spec.criterion.parameters,
            sample_size=spec.sample_set.sample_size,
            monte_carlo_count=spec.sample_set.samples_count,
            results_criteria=result.worker_result.results_criteria,
        )

    @override
    def _bulk_save(self, models: list[PowerModel]) -> None:
        self.result_storage.bulk_insert_data(models)
