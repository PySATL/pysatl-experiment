"""Shared implementation for parallel experiment execution steps."""

from __future__ import annotations

import functools
import importlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from line_profiler import profile
from pysatl_criterion.persistence.models.base import DataModel, IDataStorage
from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic
from typing_extensions import override

from pysatl_experiment.experiment_execution.parallel import BufferedSaver, Scheduler
from pysatl_experiment.experiment_execution.parallel.task_spec import TaskSpec
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.experiment_execution.step.execution_step.abstract_worker import WorkerResult
from pysatl_experiment.experiment_execution.step.execution_step.execution_step_data import ExecutionStepData
from pysatl_experiment.persistence.models.random_values import RandomValuesCountQuery
from pysatl_experiment.persistence.random_values_storage import AlchemyRandomValuesStorage


StepDataT = TypeVar("StepDataT", bound=ExecutionStepData)
WorkerResultT = TypeVar("WorkerResultT", bound=WorkerResult)
ExecutionResultT = TypeVar("ExecutionResultT")
ModelT = TypeVar("ModelT", bound=DataModel)
ResultStorageT = TypeVar("ResultStorageT", bound=IDataStorage)


@dataclass
class ExecutionTaskResult(Generic[WorkerResultT]):
    """Worker result coupled with the task metadata used to build storage models."""

    spec: TaskSpec
    worker_result: WorkerResultT


class MultithreadingExecutionStep(IExperimentStep, Generic[StepDataT, ExecutionResultT, ModelT, ResultStorageT], ABC):
    """Base class for execution steps that process random samples in parallel."""

    def __init__(
        self,
        experiment_id: int,
        experiment_name: str,
        step_config: list[StepDataT],
        monte_carlo_count: int,
        result_storage: ResultStorageT,
        storage_connection: str,
        parallel_workers: int,
    ) -> None:
        self.experiment_id = experiment_id
        self.experiment_name = experiment_name
        self.step_config = step_config
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.storage_connection = storage_connection
        self.parallel_workers = parallel_workers

    @profile
    @override
    def run(self) -> None:
        """Execute all configured tasks and persist worker results in batches."""
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
    def _collect_tasks(self) -> list[TaskSpec]:
        """Create serializable task specifications for worker processes."""
        pass

    @staticmethod
    @abstractmethod
    def _execute_task(spec: TaskSpec) -> ExecutionResultT:
        """Execute one task in a worker process."""
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

    @staticmethod
    def _load_samples_and_statistics(spec: TaskSpec) -> tuple[list[list[float]], AbstractGoodnessOfFitStatistic]:
        """Load random samples and instantiate the statistic described by a task spec."""
        storage = AlchemyRandomValuesStorage(spec.db_path)
        storage.init()

        generator_code = MultithreadingExecutionStep._get_sample_generator_code(spec)
        query = RandomValuesCountQuery(
            generator_code=generator_code,
            experiment_name=spec.experiment_name,
            sample_size=spec.sample_size,
            count=spec.monte_carlo_count,
            generator_parameters=spec.sample_generator_parameters,
        )

        rows = storage.get_count_data(query)
        if rows is None or len(rows) < spec.monte_carlo_count:
            raise ValueError("Not enough data in storage.")

        sample_data = [row.data for row in rows]
        stat_module = importlib.import_module(spec.statistic_module)
        stat_class = getattr(stat_module, spec.statistic_class_name)
        statistics = stat_class()

        return sample_data, statistics

    @staticmethod
    def _get_sample_generator_code(spec: TaskSpec) -> str:
        if spec.sample_generator_code:
            return spec.sample_generator_code
        if spec.alternative_generator:
            return spec.alternative_generator
        return spec.hypothesis_generator
