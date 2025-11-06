import functools
import time
from dataclasses import dataclass

from line_profiler import profile

from pysatl_experiment.experiment_new.step.execution.common.execution_step_data.execution_step_data import (  # noqa: E501
    ExecutionStepData,
)
from pysatl_experiment.experiment_new.step.execution.common.hypothesis_generator_data.hypothesis_generator_data import (  # noqa: E501
    HypothesisGeneratorData,
)
from pysatl_experiment.experiment_new.step.execution.common.utils.utils import get_sample_data_from_storage
from pysatl_experiment.parallel.scheduler import AdaptiveScheduler
from pysatl_experiment.parallel.task_spec import TaskSpec
from pysatl_experiment.parallel.universal_worker import universal_execute_task
from pysatl_experiment.persistence.model.random_values.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
)
from pysatl_experiment.worker.time_complexity.time_complexity import TimeComplexityWorker


@dataclass
class TimeComplexityStepData(ExecutionStepData):
    """
    Data for execution step in time complexity experiment.
    """


class TimeComplexityExecutionStep:
    """
    Standard time complexity experiment execution step.
    """

    def __init__(
        self,
        experiment_id: int,
        hypothesis_generator_data: HypothesisGeneratorData,
        step_config: list[TimeComplexityStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
        result_storage: ITimeComplexityStorage,
        storage_connection: str,
    ):
        self.experiment_id = experiment_id
        self.hypothesis_generator_data = hypothesis_generator_data
        self.step_config = step_config
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage
        self.storage_connection = storage_connection

    @profile
    def run(self) -> None:
        """
        Run time complexity experiment in parallel with buffering.
        """
        # Build task specs
        task_specs = []
        for step_data in self.step_config:
            spec = TaskSpec(
                experiment_type="time_complexity",
                statistic_class_name=step_data.statistics.__class__.__name__,
                statistic_module=step_data.statistics.__class__.__module__,
                sample_size=step_data.sample_size,
                monte_carlo_count=self.monte_carlo_count,
                db_path= self.storage_connection,
                hypothesis_generator=self.hypothesis_generator_data.generator_name,
                hypothesis_parameters=self.hypothesis_generator_data.parameters,
            )
            task_specs.append(spec)

        # Convert to zero-arg callables
        tasks = [functools.partial(universal_execute_task, spec) for spec in task_specs]

        # Buffering config
        total_tasks = len(tasks)
        BUFFER_SIZE = max(1, min(20, total_tasks // 2))
        result_buffer = []

        def flush_buffer():
            for res in result_buffer:
                exp_type, criterion_code, sample_size, results_times = res
                self._save_result_to_storage(
                    experiment_id=self.experiment_id,
                    criterion_code=criterion_code,
                    sample_size=sample_size,
                    monte_carlo_count=self.monte_carlo_count,
                    results_times=results_times,
                )
            result_buffer.clear()

        # Run with streaming and buffering
        with AdaptiveScheduler(max_workers=4) as scheduler:
            for result in scheduler.iterate_results(tasks):
                result_buffer.append(result)
                if len(result_buffer) >= BUFFER_SIZE:
                    flush_buffer()

        # Flush remaining
        if result_buffer:
            flush_buffer()


    def _save_result_to_storage(
        self,
        experiment_id: int,
        criterion_code: str,
        sample_size: int,
        monte_carlo_count: int,
        results_times: list[float],
    ) -> None:
        """
        Save results times to storage.

        :param experiment_id: experiment id.
        :param criterion_code: criterion code.
        :param sample_size: sample size.
        :param monte_carlo_count: monte carlo count.
        :param results_times: results times.

        :return: None.
        """

        data_to_save = TimeComplexityModel(
            experiment_id=experiment_id,
            criterion_code=criterion_code,
            criterion_parameters=[],
            sample_size=sample_size,
            monte_carlo_count=monte_carlo_count,
            results_times=results_times,
        )

        self.result_storage.insert_data(data_to_save)
