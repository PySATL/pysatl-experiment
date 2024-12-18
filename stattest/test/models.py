from abc import ABC, abstractmethod
from typing import Optional

from numpy import float64


class AbstractTestStatistic(ABC):
    @staticmethod
    @abstractmethod
    def code() -> str:
        """
        Generate code for test statistic.
        """
        raise NotImplementedError("Method is not implemented")

    @abstractmethod
    def execute_statistic(self, rvs, **kwargs) -> float or float64:
        """
        Execute test statistic and return calculated statistic value.
        :param rvs: rvs data to calculated statistic value
        :param kwargs: arguments for statistic calculation
        """
        raise NotImplementedError("Method is not implemented")

    def calculate_critical_value(self, rvs_size, sl) -> Optional[float] or Optional[float64]:
        """
        Calculate critical value for test statistics
        :param rvs_size: rvs size
        :param sl: significance level
        """
        return None
