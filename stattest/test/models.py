from abc import ABC, abstractmethod

from numpy import float64


class AbstractTestStatistic(ABC):
    two_tailed: bool = False

    @staticmethod
    @abstractmethod
    def code() -> str:
        """
        Generate code for test statistic.
        """
        raise NotImplementedError("Method is not implemented")

    @abstractmethod
    def execute_statistic(self, rvs, **kwargs) -> float | float64:
        """
        Execute test statistic and return calculated statistic value.
        :param rvs: rvs data to calculated statistic value
        :param kwargs: arguments for statistic calculation
        """
        raise NotImplementedError("Method is not implemented")

    def calculate_critical_value(self, rvs_size, sl) -> float | None | float64 | None:
        """
        Calculate critical value for test statistics
        :param rvs_size: rvs size
        :param sl: significance level
        """
        return None

    def calculate_two_tailed_critical_values(self, rvs_size: int, sl) -> tuple[float, float] | None:
        """
        Calculate two-tailed critical values for test statistics
        :param rvs_size: rvs size
        :param sl: significance level
        """
        return None
