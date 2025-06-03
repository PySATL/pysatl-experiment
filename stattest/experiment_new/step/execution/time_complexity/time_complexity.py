from dataclasses import dataclass

from stattest.experiment_new.step.execution.common.execution_step_data.execution_step_data import (
    ExecutionStepData,
)
from stattest.persistence.model.random_values.random_values import IRandomValuesStorage
from stattest.persistence.model.time_complexity.time_complexity import ITimeComplexityStorage
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
        worker: TimeComplexityWorker,
        step_data: list[TimeComplexityStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
        result_storage: ITimeComplexityStorage,
    ):
        self.worker = worker
        self.step_data = step_data
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage

    def run(self) -> None:
        """
        Run standard time complexity execution step.
        """
        raise NotImplementedError("Method is not yet implemented")
