from abc import ABC

from typing_extensions import override

from stattest.test.models import AbstractTestStatistic


class AbstractGoodnessOfFitTestStatistic(AbstractTestStatistic, ABC):

    @staticmethod
    @override
    def code():
        return 'GOODNESS_OF_FIT'

    def _generate(self, size):
        raise NotImplementedError("Method is not implemented")

    def test(self, rvs, alpha):  # TODO: separate abstract class for testing?
        x_cr = self.calculate_critical_value(len(rvs), alpha)
        statistic = self.execute_statistic(rvs)

        return False if statistic > x_cr else True
