"""
Power analysis worker module.

This module provides a worker implementation that evaluates the
statistical power of a hypothesis test using Monte Carlo samples
and precomputed critical values stored in a database.
"""

from dataclasses import dataclass

from pysatl_criterion.hypothesis_testing.alternative_factory.alternative_factories import AbstractAlternativeFactory
from pysatl_criterion.persistence.models.limit_distribution import CriticalValueQuery, ILimitDistributionStorage
from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic

from pysatl_experiment.experiment_execution.step.execution_step.abstract_worker import IWorker, WorkerResult


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
    limit_distribution_storage : ILimitDistributionStorage
        Storage that provides the statistic's limit distribution.

    Attributes
    ----------
    statistics : AbstractGoodnessOfFitStatistic
        Statistic instance used in testing.
    sample_data : list[list[float]]
        Input samples.
    significance_level : float
        Alpha level for tests.
    limit_distribution_storage : ILimitDistributionStorage
        Storage that provides the statistic's limit distribution.
    """

    def __init__(
        self,
        statistics: AbstractGoodnessOfFitStatistic,
        sample_data: list[list[float]],
        significance_level: float,
        limit_distribution_storage: ILimitDistributionStorage,
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
        limit_distribution_storage : ILimitDistributionStorage
            Storage that provides the statistic's limit distribution.
        """
        self.statistics = statistics
        self.sample_data = sample_data
        self.significance_level = significance_level
        self.limit_distribution_storage = limit_distribution_storage

    def execute(self) -> PowerWorkerResult:
        """
        Execute power computation across all samples.

        Returns
        -------
        PowerWorkerResult
            Results indicating whether hypothesis was rejected for each sample.
        """
        if not self.sample_data:
            return PowerWorkerResult(results_criteria=[])

        statistic = self.statistics
        sample_size = len(self.sample_data[0])

        model = self.limit_distribution_storage.get_data_for_cv(
            CriticalValueQuery(criterion_code=statistic.code(), sample_size=sample_size)
        )
        if model is None:
            raise ValueError(
                f"Limit distribution for {statistic.code()} at n={sample_size} not found in storage. "
                "Run the critical_value experiment first."
            )

        factory = AbstractAlternativeFactory.get_concrete_factory(statistic.alternative().type())
        critical_value = factory.get_critical_value_calculator().calculate(
            model.results_statistics, self.significance_level
        )
        region = factory.get_critical_area(critical_value)

        results_criteria = [
            not region.contains(statistic.execute_statistic(sample))
            for sample in self.sample_data
        ]

        return PowerWorkerResult(results_criteria=results_criteria)


# TODO: wrong types, should be fixed!!!!!!!
# TODO: check tests with db and w/o
