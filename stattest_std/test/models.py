from numpy import float64
from typing_extensions import Optional


class AbstractTestStatistic:
    @staticmethod
    def code() -> str:
        """
        Generate code for test statistic.
        """
        raise NotImplementedError("Method is not implemented")

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
        pass
