from typing import override

import numpy as np
import scipy.stats as scipy_stats

from stattest_ext.src.tests_generators.stat_gen import StatisticGenerator
from stattest_std.src.stat_tests.goodness_test import GoodnessOfFitTest


class StatGenGoodnessOfFitTest(StatisticGenerator):
    def __init__(self, criterion: GoodnessOfFitTest):
        super().__init__(criterion)
        self.criterion = criterion

    @override
    def test(self, rvs, alpha):
        x_cr = self.calculate_critical_value(len(rvs), alpha)
        statistic = self.criterion.execute_statistic(rvs)

        return False if statistic > x_cr else True

    @override
    def calculate_critical_value(self, rvs_size, alpha, count=1_000_000):
        keys_cr = [self.code(), str(rvs_size), str(alpha)]
        x_cr = self.criterion.cache.get_with_level(keys_cr)
        if x_cr is not None:
            return x_cr

        d = self._get_distribution_from_cache(rvs_size, alpha, keys_cr)
        if d is not None:
            return d

        return self._get_statistic(rvs_size, alpha, keys_cr, count)

    def _get_statistic(self, rvs_size, alpha, keys_cr, count):
        result = np.zeros(count)

        for i in range(count):
            x = self.generate(rvs_size)
            result[i] = self.criterion.execute_statistic(x)

        result.sort()

        ecdf = scipy_stats.ecdf(result)
        x_cr = np.quantile(ecdf.cdf.quantiles, q=1 - alpha)
        self.criterion.cache.put_with_level(keys_cr, x_cr)
        self.criterion.cache.put_distribution(self.criterion.code(), rvs_size, result)
        self.criterion.cache.flush()
        return x_cr

    def _get_distribution_from_cache(self, rvs_size, alpha, keys_cr):
        return self.criterion._get_distribution_from_cache(rvs_size, alpha, keys_cr)
