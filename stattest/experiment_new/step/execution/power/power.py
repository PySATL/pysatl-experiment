from dataclasses import dataclass

from stattest.experiment.generator import AbstractRVSGenerator
from stattest.experiment_new.step.execution.common.execution_step_data.execution_step_data import ExecutionStepData
from stattest.persistence.model.power.power import IPowerStorage
from stattest.persistence.model.random_values.random_values import IRandomValuesStorage
from stattest.worker.power.power import PowerWorker


@dataclass
class PowerStepData(ExecutionStepData):
    """
    Data for execution step in power experiment.
    """
    alternative: AbstractRVSGenerator
    significance_level: float


class PowerExecutionStep:
    """
    Standard power experiment execution step.
    """

    def __init__(self, worker: PowerWorker, step_data: list[PowerStepData], monte_carlo_count: int,
                 data_storage: IRandomValuesStorage, result_storage: IPowerStorage):
        self.worker = worker
        self.step_data = step_data
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage

    def run(self) -> None:
        """
        Run standard power execution step.
        """
        pass
