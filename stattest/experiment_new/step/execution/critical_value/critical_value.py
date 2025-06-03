from dataclasses import dataclass

from pysatl_criterion.persistence.model.limit_distribution.limit_distribution import (
    ILimitDistributionStorage,
)

from stattest.experiment_new.step.execution.common.execution_step_data.execution_step_data import (
    ExecutionStepData,
)
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
        worker: CriticalValueWorker,
        step_data: list[CriticalValueStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
        result_storage: ILimitDistributionStorage,
    ):
        self.worker = worker
        self.step_data = step_data
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage

    def run(self) -> None:
        """
        Run standard critical value execution step.
        """
        pass
