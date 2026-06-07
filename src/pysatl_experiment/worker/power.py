"""
Power analysis worker module.

This module provides a worker implementation that evaluates the
statistical power of a hypothesis test using Monte Carlo samples
and precomputed critical values stored in a database.
"""

from dataclasses import dataclass

from pysatl_criterion import GoodnessOfFitTest
from pysatl_criterion.hypothesis_testing.critical_values.resolver.storage_resolver import StorageCriticalValueResolver
from pysatl_criterion.persistence.sqlalchemy.datastorage import AlchemyLimitDistributionStorage
from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic

from pysatl_experiment.worker.model.abstract_worker import IWorker, WorkerResult


@dataclass
class PowerWorkerResult(WorkerResult):
    """
    Result container for power worker.

    Attributes
    ----------
    results_criteria : list[bool]
        Boolean outcomes indicating whether hypothesis was rejected
        for each sample.
    """

    results_criteria: list[bool]


class PowerWorker(IWorker[PowerWorkerResult]):
    """
    Worker for computing statistical power of a hypothesis test.

    This worker evaluates whether a given test correctly rejects or
    accepts the null hypothesis across multiple samples using precomputed
    critical values stored in a database.

    Parameters
    ----------
    statistics : AbstractGoodnessOfFitStatistic
        Statistic used in hypothesis testing.
    sample_data : list[list[float]]
        Generated samples for evaluation.
    significance_level : float
        Significance level (alpha) used for hypothesis testing.
    storage_connection : str
        Connection string to SQLite database containing critical values.

    Attributes
    ----------
    statistics : AbstractGoodnessOfFitStatistic
        Statistic instance used in testing.
    sample_data : list[list[float]]
        Input samples.
    significance_level : float
        Alpha level for tests.
    storage_connection : str
        Database connection string.
    """

    def __init__(
        self,
        statistics: AbstractGoodnessOfFitStatistic,
        sample_data: list[list[float]],
        significance_level: float,
        storage_connection: str,
    ):
        """
        Initialize power worker.

        Parameters
        ----------
        statistics : AbstractGoodnessOfFitStatistic
            Statistic used in testing.
        sample_data : list[list[float]]
            Input datasets.
        significance_level : float
            Alpha level for hypothesis testing.
        storage_connection : str
            SQLAlchemy database connection string.
        """
        self.statistics = statistics
        self.sample_data = sample_data
        self.significance_level = significance_level
        self.storage_connection = storage_connection

    def execute(self) -> PowerWorkerResult:
        """
        Execute power computation across all samples.

        Returns
        -------
        PowerWorkerResult
            Results indicating whether hypothesis was rejected for each sample.
        """
        storage = AlchemyLimitDistributionStorage(self.storage_connection)
        storage.init()

        cv_resolver = StorageCriticalValueResolver(storage)

        gof_test = GoodnessOfFitTest(
            statistics=[self.statistics],
            significance_level=self.significance_level,
            cv_resolver=cv_resolver,
        )

        results_criteria = []
        for sample in self.sample_data:
            result = gof_test.test(sample)
            results_criteria.append(result)

        worker_result = PowerWorkerResult(results_criteria=results_criteria)

        return worker_result


# TODO: wrong types, should be fixed!!!!!!!
# TODO: check tests with db and w/o
