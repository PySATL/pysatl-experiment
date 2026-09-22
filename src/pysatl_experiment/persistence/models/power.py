"""Power storage models and interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass

from pysatl_criterion.persistence.models.base import DataModel, DataQuery, IDataStorage

from pysatl_experiment.configuration.models.parameters import NumericParameters


@dataclass
class PowerModel(DataModel):
    """
    Power analysis result model.

    Parameters
    ----------
    experiment_id : int
        Experiment identifier.
    criterion_code : str
        Statistical criterion code.
    criterion_parameters : NumericParameters
        Parameters of criterion.
    sample_size : int
        Sample size.
    alternative_code : str
        Alternative hypothesis code.
    alternative_parameters : NumericParameters
        Parameters of alternative hypothesis.
    monte_carlo_count : int
        Number of simulations.
    significance_level : float
        Significance level alpha.
    results_criteria : list[bool]
        Simulation results (rejections / non-rejections).
    """

    experiment_id: int
    criterion_code: str
    criterion_parameters: NumericParameters
    sample_size: int
    alternative_code: str
    alternative_parameters: NumericParameters
    monte_carlo_count: int
    significance_level: float
    results_criteria: list[bool]


@dataclass
class PowerQuery(DataQuery):
    """
    Query for retrieving power results.

    Parameters
    ----------
    criterion_code : str
    criterion_parameters : NumericParameters
    sample_size : int
    alternative_code : str
    alternative_parameters : NumericParameters
    monte_carlo_count : int
    significance_level : float
    """

    criterion_code: str
    criterion_parameters: NumericParameters
    sample_size: int
    alternative_code: str
    alternative_parameters: NumericParameters
    monte_carlo_count: int
    significance_level: float


class IPowerStorage(IDataStorage[PowerModel, PowerQuery], ABC):
    """Power storage interface."""

    @abstractmethod
    def bulk_insert_data(self, data_list: Iterable[PowerModel]) -> None:
        """
        Insert or update multiple power records.

        Parameters
        ----------
        data_list : Iterable[PowerModel]
            Power results to store.
        """
        pass
