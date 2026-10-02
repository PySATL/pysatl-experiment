"""Storage dependencies created and initialized by experiment factories."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from pysatl_criterion.persistence.models.base import IDataStorage

from pysatl_experiment.persistence.contracts.experiment import IExperimentStorage
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage


ResultStorageT = TypeVar("ResultStorageT", bound=IDataStorage)


@dataclass(frozen=True)
class ExperimentStorages(Generic[ResultStorageT]):
    """Initialized stores shared by run preparation, planning and steps."""

    data: IRandomValuesStorage
    result: ResultStorageT
    experiment: IExperimentStorage
