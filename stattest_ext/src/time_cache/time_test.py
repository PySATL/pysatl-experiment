from stattest_ext.src.time_cache.time_cache import TimeCacheService
from stattest_std.src.stat_tests.goodness_test import GoodnessOfFitTest


# TODO: extend to AbstractTest later
class TimeTest:
    def __init__(self, test=GoodnessOfFitTest(), time_cache=TimeCacheService()):
        self.test = test
        self.cache = test.cache
        self.time_cache = time_cache

    def test_with_time_counting(self, rvs, alpha):
        rvs_len = len(rvs)

        x_cr = self.test.calculate_critical_value(rvs_len, alpha)

        start = self.time_cache.count_time()
        statistic = self.test.execute_statistic(rvs)
        stop = self.time_cache.count_time()

        time = stop - start
        self.time_cache.put_time(self.test.code(), rvs_len, [time])

        return False if statistic > x_cr else True
