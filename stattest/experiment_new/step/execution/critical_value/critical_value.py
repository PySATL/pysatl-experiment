from dataclasses import dataclass

from pysatl_criterion.persistence.model.limit_distribution.limit_distribution import (
    ILimitDistributionStorage,
    LimitDistributionModel,
)
from stattest.experiment_new.step.execution.common.execution_step_data.execution_step_data import (
    ExecutionStepData,
)
from stattest.experiment_new.step.execution.common.hypothesis_generator_data.hypothesis_generator_data import (
    HypothesisGeneratorData,
)
from stattest.experiment_new.step.execution.common.utils.utils import get_sample_data_from_storage
from stattest.persistence.model.random_values.random_values import IRandomValuesStorage
from stattest.worker.critical_value.critical_value import CriticalValueWorker


@dataclass
class CriticalValueStepData(ExecutionStepData):
    """
    Data for execution step in critical value experiment.
    """


class CriticalValueExecutionStep:
    """
    Standard critical value experiment execution step.
    """

    def __init__(
        self,
        experiment_id: int,
        hypothesis_generator_data: HypothesisGeneratorData,
        step_config: list[CriticalValueStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
        result_storage: ILimitDistributionStorage,
    ):
        self.experiment_id = experiment_id
        self.hypothesis_generator_data = hypothesis_generator_data
        self.step_config = step_config
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage

    def run(self) -> None:
        """
        Run standard critical value execution step.
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

            worker = CriticalValueWorker(statistics=statistics, sample_data=data)
            result = worker.execute()
            results_statistics = result.results_statistics

            self._save_result_to_storage(
                experiment_id=self.experiment_id,
                criterion_code=statistics.code(),
                sample_size=sample_size,
                monte_carlo_count=self.monte_carlo_count,
                results_statistics=results_statistics,
            )

    def _save_result_to_storage(
        self,
        experiment_id: int,
        criterion_code: str,
        sample_size: int,
        monte_carlo_count: int,
        results_statistics: list[float],
    ) -> None:
        """
        Save results statistics to storage.

        :param experiment_id: experiment id.
        :param criterion_code: criterion code.
        :param sample_size: sample size.
        :param monte_carlo_count: monte carlo count.
        :param results_statistics: results statistics.

        :return: None.
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
