import functools
from dataclasses import dataclass

from line_profiler import profile

from pysatl_experiment.configuration.model.alternative.alternative import Alternative
from pysatl_experiment.experiment_new.step.execution.common.execution_step_data.execution_step_data import (
    ExecutionStepData,
)
from pysatl_experiment.parallel.buffered_saver import BufferedSaver
from pysatl_experiment.parallel.scheduler import Scheduler
from pysatl_experiment.parallel.task_spec import TaskSpec
from pysatl_experiment.parallel.universal_worker import universal_execute_task
from pysatl_experiment.persistence.model.power.power import IPowerStorage, PowerModel
from pysatl_experiment.persistence.model.random_values.random_values import IRandomValuesStorage


@dataclass
class PowerStepData(ExecutionStepData):
    """
    Data for execution step in power experiment.
    """

    alternative: Alternative
    significance_level: float


class PowerExecutionStep:
    """
    Standard power experiment execution step.
    """

    def __init__(
        self,
        experiment_id: int,
        step_config: list[PowerStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
        result_storage: IPowerStorage,
        storage_connection: str,
        parallel_workers: int,
    ):
        self.experiment_id = experiment_id
        self.step_config = step_config
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage
        self.storage_connection = storage_connection
        self.parallel_workers = parallel_workers

    @profile
    def run(self) -> None:
        """
        Run power experiment in parallel with buffering.
        """

        task_specs = []
        for step_data in self.step_config:
            spec = TaskSpec(
                experiment_type="power",
                statistic_class_name=step_data.statistics.__class__.__name__,
                statistic_module=step_data.statistics.__class__.__module__,
                sample_size=step_data.sample_size,
                monte_carlo_count=self.monte_carlo_count,
                db_path=self.storage_connection,
                alternative_generator=step_data.alternative.generator_name,
                alternative_parameters=step_data.alternative.parameters,
                significance_level=step_data.significance_level,
            )
            task_specs.append(spec)

        tasks = [functools.partial(universal_execute_task, spec) for spec in task_specs]

        def save_batch(results_batch: list):
            for res in results_batch:
                (
                    exp_type,
                    criterion_code,
                    sample_size,
                    results_criteria,
                    alt_generator,
                    alt_parameters,
                    sig_level,
                ) = res
                alternative = Alternative(generator_name=alt_generator, parameters=alt_parameters)
                self._save_result_to_storage(
                    criterion_code=criterion_code,
                    sample_size=sample_size,
                    alternative=alternative,
                    significance_level=sig_level,
                    results_criteria=results_criteria,
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

    def _save_result_to_storage(
        self,
        criterion_code: str,
        sample_size: int,
        alternative: Alternative,
        significance_level: float,
        results_criteria: list[bool],
    ) -> None:
        """
        Save result to power storage.
        """

        query = PowerModel(
            experiment_id=self.experiment_id,
            criterion_code=criterion_code,
            criterion_parameters=[],
            sample_size=sample_size,
            alternative_code=alternative.generator_name,
            alternative_parameters=alternative.parameters,
            monte_carlo_count=self.monte_carlo_count,
            significance_level=significance_level,
            results_criteria=results_criteria,
        )

        storage = self.result_storage
        storage.insert_data(query)
