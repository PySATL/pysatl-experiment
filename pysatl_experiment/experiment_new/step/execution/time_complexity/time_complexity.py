import functools
from dataclasses import dataclass

from line_profiler import profile

from pysatl_experiment.experiment_new.step.execution.common.execution_step_data.execution_step_data import (  # noqa: E501
    ExecutionStepData,
)
from pysatl_experiment.experiment_new.step.execution.common.hypothesis_generator_data.hypothesis_generator_data import (  # noqa: E501
    HypothesisGeneratorData,
)
from pysatl_experiment.parallel.buffered_saver import BufferedSaver
from pysatl_experiment.parallel.scheduler import AdaptiveScheduler
from pysatl_experiment.parallel.task_spec import TaskSpec
from pysatl_experiment.parallel.universal_worker import universal_execute_task
from pysatl_experiment.persistence.model.random_values.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
)


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

        task_specs = []
        for step_data in self.step_config:
            spec = TaskSpec(
                experiment_type="time_complexity",
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
                exp_type, criterion_code, sample_size, results_times = res
                self._save_result_to_storage(
                    experiment_id=self.experiment_id,
                    criterion_code=criterion_code,
                    sample_size=sample_size,
                    monte_carlo_count=self.monte_carlo_count,
                    results_times=results_times,
                )

        total_tasks = len(tasks)
        buffer_size = max(1, min(20, total_tasks // 2))
        saver = BufferedSaver(save_func=save_batch, buffer_size=buffer_size)

        with AdaptiveScheduler() as scheduler:
            for result in scheduler.iterate_results(tasks):
                saver.add(result)

        saver.flush()

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
