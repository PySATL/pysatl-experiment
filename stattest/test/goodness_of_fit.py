from typing import override

import numpy as np
import scipy.stats as scipy_stats

from stattest.test.models import AbstractTestStatistic
from stattest.persistence.json_store.cache import MonteCarloCacheService


class AbstractGoodnessOfFitTestStatistic(AbstractTestStatistic):
    def __init__(self, cache=MonteCarloCacheService()):
        self.cache = cache

    @staticmethod
    @override
    def code():
        return 'GOODNESS_OF_FIT'

    @override
    def calculate_critical_value(self, rvs_size, sl, count=1_000_000):
        keys_cr = [self.code(), str(rvs_size), str(sl)]
        x_cr = self.cache.get_with_level(keys_cr)
        if x_cr is not None:
            return x_cr

        d = self._get_distribution_from_cache(rvs_size, sl, keys_cr)
        if d is not None:
            return d

        return self._get_statistic(rvs_size, sl, keys_cr, count)

    def _get_distribution_from_cache(self, rvs_size, alpha, keys_cr):
        d = self.cache.get_distribution(self.code(), rvs_size)
        if d is not None:
            ecdf = scipy_stats.ecdf(d)
            x_cr = np.quantile(ecdf.cdf.quantiles, q=1 - alpha)
            self.cache.put_with_level(keys_cr, x_cr)
            self.cache.flush()
            return x_cr
        else:
            return d

    # TODO: separate generator class!
    def _get_statistic(self, rvs_size, alpha, keys_cr, count):
        result = np.zeros(count)

        for i in range(count):
            x = self._generate(rvs_size)
            result[i] = self.execute_statistic(x, )

        result.sort()

        ecdf = scipy_stats.ecdf(result)
        x_cr = np.quantile(ecdf.cdf.quantiles, q=1 - alpha)
        self.cache.put_with_level(keys_cr, x_cr)
        self.cache.put_distribution(self.code(), rvs_size, result)
        self.cache.flush()
        return x_cr

    def _generate(self, size):
        raise NotImplementedError("Method is not implemented")

    def test(self, rvs, alpha):  # TODO: separate abstract class for testing?
        x_cr = self.calculate_critical_value(len(rvs), alpha)
        statistic = self.execute_statistic(rvs)

        return False if statistic > x_cr else True
