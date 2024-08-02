from typing import override

from stattest_std.src.stat_tests.abstract_test import AbstractTest


class StatisticGenerator(AbstractTest):
    def __init__(self, criterion: AbstractTest):
        self.criterion = criterion

    def code(self):
        return self.criterion.code()

    def generate(self, size):
        raise NotImplementedError("Method is not implemented")

    @override
    def test(self, rvs, alpha):
        return self.criterion.test(rvs, alpha)

    @override
    def execute_statistic(self, rvs, **kwargs):
        return self.criterion.execute_statistic(rvs, **kwargs)

    @override
    def calculate_critical_value(self, rvs_size, alpha, count=500_000):
        return self.criterion.calculate_critical_value(rvs_size, alpha, count)
