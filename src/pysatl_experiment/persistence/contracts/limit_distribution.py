"""Storage contract for experiment-owned empirical limit distributions."""

from abc import ABC

from pysatl_criterion.persistence.models.base import IDataStorage

from pysatl_experiment.persistence.models.limit_distribution import LimitDistributionModel, LimitDistributionQuery


class ILimitDistributionStorage(IDataStorage[LimitDistributionModel, LimitDistributionQuery], ABC):
    """Read and write results scoped by experiment name."""
