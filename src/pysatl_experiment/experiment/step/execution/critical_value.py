"""Critical value experiment execution step implementation."""

import functools
from dataclasses import dataclass

from line_profiler import profile
from pysatl_criterion.persistence.models.limit_distribution import ILimitDistributionStorage, LimitDistributionModel

from src.pysatl_experiment.configuration.model.experiment_type import ExperimentType
from src.pysatl_experiment.experiment.model.experiment_step import IExperimentStep
from src.pysatl_experiment.experiment.step.execution.common.execution_step_data import ExecutionStepData
from src.pysatl_experiment.experiment.step.execution.common.hypothesis_generator_data import HypothesisGeneratorData
from src.pysatl_experiment.parallel.buffered_saver import BufferedSaver
from src.pysatl_experiment.parallel.scheduler import Scheduler
from src.pysatl_experiment.parallel.task_spec import TaskSpec
from src.pysatl_experiment.parallel.universal_worker import universal_execute_task
from src.pysatl_experiment.persistence.model.random_values import IRandomValuesStorage


@dataclass
class CriticalValueStepData(ExecutionStepData):
    """Data for a single execution step in critical value experiment."""


class CriticalValueExecutionStep(IExperimentStep):
    """
    Execute critical value experiment execution step.

    The step loads generated samples, runs statistical criteria,
    and stores empirical limit distributions.
    """

    def __init__(
        self,
        experiment_id: int,
        hypothesis_generator_data: HypothesisGeneratorData,
        step_config: list[CriticalValueStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
        result_storage: ILimitDistributionStorage,
        storage_connection: str,
        parallel_workers: int,
    ) -> None:
        """
        Initialize critical value execution step.

        Parameters
        ----------
        experiment_id : int
            Experiment identifier.
        hypothesis_generator_data : HypothesisGeneratorData
            Hypothesis generator metadata.
        step_config : list[CriticalValueStepData]
            Execution task configurations.
        monte_carlo_count : int
            Number of Monte Carlo iterations.
        data_storage : IRandomValuesStorage
            Storage containing generated samples.
        result_storage : ILimitDistributionStorage
            Storage for limit distributions.
        storage_connection : str
            Database connection string.
        parallel_workers : int
            Number of parallel worker processes.
        """
        self.experiment_id = experiment_id
        self.hypothesis_generator_data = hypothesis_generator_data
        self.step_config = step_config
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage
        self.storage_connection = storage_connection
        self.parallel_workers = parallel_workers

    @profile
    def run(self) -> None:
        """
        Execute all critical value tasks in parallel.

        Tasks are buffered before saving in order to reduce
        storage overhead.
        """
        task_specs = []
        for step_data in self.step_config:
            spec = TaskSpec(
                experiment_type=ExperimentType.CRITICAL_VALUE,
                statistic_class_name=step_data.statistics.__class__.__name__,
                statistic_module=step_data.statistics.__class__.__module__,
                sample_size=step_data.sample_size,
                monte_carlo_count=self.monte_carlo_count,
                db_path=self.storage_connection,
                hypothesis_generator=self.hypothesis_generator_data.generator_name,
                hypothesis_parameters=self.hypothesis_generator_data.parameters,
            )
            task_specs.append(spec)

        tasks = [functools.partial(universal_execute_task, spec) for spec in task_specs]

        def save_batch(results_batch: list):
            for res in results_batch:
                exp_type, criterion_code, sample_size, results_statistics = res
                self._save_result_to_storage(
                    experiment_id=self.experiment_id,
                    criterion_code=criterion_code,
                    sample_size=sample_size,
                    monte_carlo_count=self.monte_carlo_count,
                    results_statistics=results_statistics,
                )

        total_tasks = len(tasks)
        buffer_size = max(1, min(20, total_tasks // 2))
        saver = BufferedSaver(save_func=save_batch, buffer_size=buffer_size)

        try:
            with Scheduler(max_workers=self.parallel_workers) as scheduler:
                for result in scheduler.iterate_results(tasks):
                    saver.add(result)
        finally:
            saver.flush()

    @profile
    def _save_result_to_storage(
        self,
        experiment_id: int,
        criterion_code: str,
        sample_size: int,
        monte_carlo_count: int,
        results_statistics: list[float],
    ) -> None:
        """
        Save calculated limit distribution to storage.

        Parameters
        ----------
        experiment_id : int
            Experiment identifier.
        criterion_code : str
            Statistical criterion identifier.
        sample_size : int
            Sample size.
        monte_carlo_count : int
            Number of Monte Carlo iterations.
        results_statistics : list[float]
            Calculated statistic values.
        """
        data_to_save = LimitDistributionModel(
            experiment_id=experiment_id,
            criterion_code=criterion_code,
            criterion_parameters=[],
            sample_size=sample_size,
            monte_carlo_count=monte_carlo_count,
            results_statistics=results_statistics,
        )

        self.result_storage.insert_data(data_to_save)
