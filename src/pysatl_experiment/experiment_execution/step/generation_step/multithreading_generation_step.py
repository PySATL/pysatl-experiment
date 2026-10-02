"""Shared implementation for parallel random sample generation steps."""

from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from line_profiler import profile
from pysatl_criterion.persistence.models.base import DataModel
from typing_extensions import override

from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.experiment_execution.step.progress import StepProgress
from pysatl_experiment.loggers.rich_console import get_rich_console
from pysatl_experiment.parallel import BufferedSaver, Scheduler, no_context


StepDataT = TypeVar("StepDataT")
TaskSpecT = TypeVar("TaskSpecT")
GenerationResultT = TypeVar("GenerationResultT")
ModelT = TypeVar("ModelT", bound=DataModel)
ResultStorageT = TypeVar("ResultStorageT")


class MultithreadingGenerationStep(
    IExperimentStep,
    Generic[StepDataT, TaskSpecT, GenerationResultT, ModelT, ResultStorageT],
    ABC,
):
    """Base class for generation steps that create random samples in parallel."""

    def __init__(
        self,
        step_config: list[StepDataT],
        result_storage: ResultStorageT,
        parallel_workers: int,
        *,
        total_samples: int,
        write_batch_size: int = 1000,
    ) -> None:
        self.step_config = step_config
        self.result_storage = result_storage
        self.parallel_workers = parallel_workers
        self.write_batch_size = write_batch_size
        self.total_samples = total_samples

    @profile
    @override
    def run(self) -> None:
        """Execute all configured generation tasks and persist results in batches."""
        console = get_rich_console(stderr=True)
        if self.total_samples == 0:
            console.print("All samples already exist; generation is not required.")
            return

        task_specs = self._collect_tasks()
        tasks = (functools.partial(type(self)._execute_task, spec) for spec in task_specs)

        with StepProgress(
            self.total_samples,
            description="Generating data",
            processed_label="Generated",
            advance_on="saved",
        ) as progress:

            def save_with_progress(models: list[ModelT]) -> None:
                self._bulk_save(models)
                progress.saved(len(models))

            saver = BufferedSaver(save_func=save_with_progress, buffer_size=self.write_batch_size)
            with Scheduler(max_workers=self.parallel_workers, context_factory=no_context) as scheduler:
                for result in scheduler.iterate_results(tasks):
                    models = self._to_models(result)
                    progress.processed(len(models))
                    saver.extend(models)
            saver.flush()

    @abstractmethod
    def _collect_tasks(self) -> Iterable[TaskSpecT]:
        """Create serializable task specifications for worker processes."""
        pass

    @staticmethod
    @abstractmethod
    def _execute_task(spec: TaskSpecT, context: None) -> GenerationResultT:
        """Execute one generation task in a worker process."""
        pass

    @abstractmethod
    def _to_models(self, result: GenerationResultT) -> list[ModelT]:
        """Convert one worker result into persistence models."""
        pass

    @abstractmethod
    def _bulk_save(self, models: list[ModelT]) -> None:
        """Persist prepared models in one storage batch."""
        pass
