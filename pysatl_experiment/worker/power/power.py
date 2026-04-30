from dataclasses import dataclass

from pysatl_criterion.critical_value.resolver.storage_resolver import StorageCriticalValueResolver
from pysatl_criterion.persistence.limit_distribution.datastorage.datastorage import AlchemyLimitDistributionStorage
from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic
from pysatl_criterion.test.goodness_of_fit_test.goodness_of_fit_test import GoodnessOfFitTest

from pysatl_experiment.worker.model.abstract_worker.abstract_worker import IWorker, WorkerResult


@dataclass
class PowerWorkerResult(WorkerResult):
    """
    Power worker result container.
    """

    results_criteria: list[bool]


class PowerWorker(IWorker[PowerWorkerResult]):
    """
    Power worker.
    """

    def __init__(
        self,
        statistics: AbstractGoodnessOfFitStatistic,
        sample_data: list[list[float]],
        significance_level: float,
        storage_connection: str,
    ):
        self.statistics = statistics
        self.sample_data = sample_data
        self.significance_level = significance_level
        self.storage_connection = storage_connection

    def execute(self) -> PowerWorkerResult:
        """
        Execute power worker.
        """

        storage = AlchemyLimitDistributionStorage(self.storage_connection)
        storage.init()

        cv_resolver = StorageCriticalValueResolver(storage)

        gof_test = GoodnessOfFitTest(
            statistics=self.statistics,
            significance_level=self.significance_level,
            cv_resolver=cv_resolver,
        )

        results_criteria = []
        for sample in self.sample_data:
            result = gof_test.test(sample)
            results_criteria.append(result)

        worker_result = PowerWorkerResult(results_criteria=results_criteria)

        return worker_result
