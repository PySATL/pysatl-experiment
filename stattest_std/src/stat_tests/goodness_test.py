from typing import override

import numpy as np
import scipy.stats as scipy_stats

from stattest_std.src.stat_tests.abstract_test import AbstractTest
from stattest_std.src.cache_services.cache import MonteCarloCacheService


class GoodnessOfFitTest(AbstractTest):
    def __init__(self, cache=MonteCarloCacheService()):
        self.cache = cache

    @staticmethod
    @override
    def code():
        return '_gof'

    @override
    def calculate_critical_value(self, rvs_size, alpha, count=1_000_000):
        keys_cr = [self.code(), str(rvs_size), str(alpha)]
        x_cr = self.cache.get_with_level(keys_cr)  # кэш
        if x_cr is not None:
            return x_cr

        d = self.__get_distribution(rvs_size, alpha, keys_cr)
        if d is not None:
            return d

        # TODO: move statistic generation to ext_package
        return self.__generate_statistic(rvs_size, alpha, keys_cr, count)

    def __get_distribution(self, rvs_size, alpha, keys_cr):
        d = self.cache.get_distribution(self.code(), rvs_size)  # TODO: move to second package??
        if d is not None:
            ecdf = scipy_stats.ecdf(d)
            x_cr = np.quantile(ecdf.cdf.quantiles, q=1 - alpha)
            self.cache.put_with_level(keys_cr, x_cr)
            self.cache.flush()
            return x_cr
        else:
            return d

    def __generate_statistic(self, rvs_size, alpha, keys_cr, count):  # TODO: move statistic generation to ext_package
        raise "Method is not implemented"

    @override
    def test(self, rvs, alpha):
        print("Calculating cvs")  # TODO remove
        x_cr = self.calculate_critical_value(len(rvs), alpha)
        print("Executing statistics")  # TODO remove

        statistic = self.execute_statistic(rvs)

        return False if statistic > x_cr else True
