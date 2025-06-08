from dataclasses import dataclass

from stattest.experiment_new.step.execution.common.execution_step_data.execution_step_data import ExecutionStepData
from stattest.experiment_new.step.execution.common.hypothesis_generator_data.hypothesis_generator_data import (
    HypothesisGeneratorData,
)
from stattest.experiment_new.step.execution.common.utils.utils import get_sample_data_from_storage
from stattest.persistence.model.random_values.random_values import IRandomValuesStorage
from stattest.persistence.model.time_complexity.time_complexity import ITimeComplexityStorage, TimeComplexityModel
from stattest.worker.time_complexity.time_complexity import TimeComplexityWorker


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
    ):
        self.experiment_id = experiment_id
        self.hypothesis_generator_data = hypothesis_generator_data
        self.step_config = step_config
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage

    def run(self) -> None:
        """
        Run standard time complexity execution step.
        """

        for step_data in self.step_config:
            statistics = step_data.statistics
            sample_size = step_data.sample_size

            data = get_sample_data_from_storage(
                generator_name=self.hypothesis_generator_data.generator_name,
                generator_parameters=self.hypothesis_generator_data.parameters,
                sample_size=sample_size,
                count=self.monte_carlo_count,
                data_storage=self.data_storage,
            )

            worker = TimeComplexityWorker(statistics=statistics, sample_data=data)
            result = worker.execute()
            results_times = result.results_times

            self._save_result_to_storage(
                experiment_id=self.experiment_id,
                criterion_code=statistics.code(),
                sample_size=sample_size,
                monte_carlo_count=self.monte_carlo_count,
                results_times=results_times,
            )

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
