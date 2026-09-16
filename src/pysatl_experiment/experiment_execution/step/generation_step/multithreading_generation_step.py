"""Shared implementation for parallel random sample generation steps."""

from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from line_profiler import profile
from pysatl_criterion.persistence.models.base import DataModel, IDataStorage
from typing_extensions import override

from pysatl_experiment.experiment_execution.parallel import BufferedSaver, Scheduler
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep


StepDataT = TypeVar("StepDataT")
TaskSpecT = TypeVar("TaskSpecT")
GenerationResultT = TypeVar("GenerationResultT")
ModelT = TypeVar("ModelT", bound=DataModel)
ResultStorageT = TypeVar("ResultStorageT", bound=IDataStorage)


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
    ) -> None:
        self.step_config = step_config
        self.result_storage = result_storage
        self.parallel_workers = parallel_workers

    @profile
    @override
    def run(self) -> None:
        """Execute all configured generation tasks and persist results in batches."""
        task_specs = self._collect_tasks()
        tasks = [functools.partial(type(self)._execute_task, spec) for spec in task_specs]

        total_tasks = len(tasks)
        buffer_size = max(1, min(20, total_tasks // 2))
        saver = BufferedSaver(save_func=self.save_batch, buffer_size=buffer_size)

        try:
            with Scheduler(max_workers=self.parallel_workers) as scheduler:
                for result in scheduler.iterate_results(tasks):
                    saver.add(result)
        finally:
            saver.flush()

    @abstractmethod
    def _collect_tasks(self) -> list[TaskSpecT]:
        """Create serializable task specifications for worker processes."""
        pass

    @staticmethod
    @abstractmethod
    def _execute_task(spec: TaskSpecT) -> GenerationResultT:
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

    def save_batch(self, results: list[GenerationResultT]) -> None:
        """Convert buffered worker results to models and persist them."""
        models: list[ModelT] = []
        for result in results:
            models.extend(self._to_models(result))

        if models:
            self._bulk_save(models)
