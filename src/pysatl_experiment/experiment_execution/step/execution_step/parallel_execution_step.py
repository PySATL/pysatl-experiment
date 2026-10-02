"""Shared scheduling and persistence for independently described execution tasks."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

from line_profiler import profile
from pysatl_criterion.persistence.models.base import DataModel, IDataStorage
from typing_extensions import override

from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.experiment_execution.step.execution_step.abstract_worker import WorkerResult
from pysatl_experiment.experiment_execution.step.progress import StepProgress
from pysatl_experiment.loggers.rich_console import get_rich_console
from pysatl_experiment.parallel import BufferedSaver, Scheduler


ContextT = TypeVar("ContextT")
TaskSpecT = TypeVar("TaskSpecT")
ExecutionResultT = TypeVar("ExecutionResultT")
ModelT = TypeVar("ModelT", bound=DataModel)
ResultStorageT = TypeVar("ResultStorageT", bound=IDataStorage)


WorkerResultT = TypeVar("WorkerResultT", bound=WorkerResult)


@dataclass
class ExecutionTaskResult(Generic[TaskSpecT, WorkerResultT]):
    """Worker result coupled with the task metadata used to build storage models."""

    spec: TaskSpecT
    worker_result: WorkerResultT


class ParallelExecutionStep(
    IExperimentStep, Generic[TaskSpecT, ExecutionResultT, ModelT, ResultStorageT, ContextT], ABC
):
    """Schedule computations and persist their results in the parent process."""

    def __init__(
        self,
        parallel_workers: int,
        result_storage: ResultStorageT,
        context_factory: Callable[[], ContextT],
        *,
        total_tasks: int,
        write_batch_size: int = 20,
    ) -> None:
        if isinstance(write_batch_size, bool) or not isinstance(write_batch_size, int) or write_batch_size <= 0:
            raise ValueError("write_batch_size must be a positive integer")
        self.parallel_workers = parallel_workers
        self.result_storage = result_storage
        self.context_factory = context_factory
        self.write_batch_size = write_batch_size
        self.total_tasks = total_tasks

    @profile
    @override
    def run(self) -> None:
        """Execute all configured tasks and persist worker results in batches."""
        if self.total_tasks == 0:
            get_rich_console(stderr=True).print("All results already exist; execution is not required.")
            return
        task_specs = self._collect_tasks()
        tasks = (self._make_task(spec) for spec in task_specs)

        with StepProgress(self.total_tasks, description="Computing", processed_label="Tasks") as progress:
            save_failed = False

            def save_with_progress(results: list[ExecutionResultT]) -> None:
                nonlocal save_failed
                # A failed write must not be retried implicitly by the final flush.
                save_failed = True
                self.save_batch(results)
                save_failed = False
                progress.saved(len(results))

            saver = BufferedSaver(save_func=save_with_progress, buffer_size=self.write_batch_size)
            try:
                with Scheduler(max_workers=self.parallel_workers, context_factory=self.context_factory) as scheduler:
                    for result in scheduler.iterate_results(tasks):
                        progress.processed(1)
                        saver.add(result)
            finally:
                if not save_failed:
                    saver.flush()

    @abstractmethod
    def _collect_tasks(self) -> Iterable[TaskSpecT]:
        """Create serializable task specifications for worker processes."""
        pass

    @abstractmethod
    def _make_task(self, spec: TaskSpecT) -> Callable[[ContextT], ExecutionResultT]:
        """Build a serializable callable without capturing the step or result store."""
        pass

    @abstractmethod
    def _to_model(self, result: ExecutionResultT) -> ModelT:
        """Convert one worker result into a persistence model."""
        pass

    @abstractmethod
    def _bulk_save(self, models: list[ModelT]) -> None:
        """Persist prepared models in one storage batch."""
        pass

    def save_batch(self, results: list[ExecutionResultT]) -> None:
        """Convert buffered worker results to models and persist them."""
        models = [self._to_model(result) for result in results]
        if models:
            self._bulk_save(models)
