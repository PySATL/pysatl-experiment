from dataclasses import dataclass

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic
from stattest.configuration.model.alternative.alternative import Alternative
from stattest.experiment_new.step.execution.common.execution_step_data.execution_step_data import (
    ExecutionStepData,
)
from stattest.experiment_new.step.execution.common.utils.utils import get_sample_data_from_storage
from stattest.persistence.model.power.power import IPowerStorage, PowerModel
from stattest.persistence.model.random_values.random_values import IRandomValuesStorage
from stattest.worker.power.power import PowerWorker


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
    ):
        self.experiment_id = experiment_id
        self.step_config = step_config
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage
        self.result_storage = result_storage
        self.storage_connection = storage_connection

    def run(self) -> None:
        """
        Run standard power execution step.
        """

        for step_data in self.step_config:
            statistics = step_data.statistics
            sample_size = step_data.sample_size
            alternative = step_data.alternative
            significance_level = step_data.significance_level

            samples = get_sample_data_from_storage(
                generator_name=alternative.generator_name,
                generator_parameters=alternative.parameters,
                sample_size=sample_size,
                count=self.monte_carlo_count,
                data_storage=self.data_storage,
            )

            worker = PowerWorker(
                statistics=statistics,
                sample_data=samples,
                significance_level=significance_level,
                storage_connection=self.storage_connection,
            )

            result = worker.execute()
            results_criteria = result.results_criteria
            self._save_result_to_storage(
                statistics=statistics,
                sample_size=sample_size,
                alternative=alternative,
                significance_level=significance_level,
                results_criteria=results_criteria,
            )

    def _save_result_to_storage(
        self,
        statistics: AbstractGoodnessOfFitStatistic,
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
            criterion_code=statistics.code(),
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
