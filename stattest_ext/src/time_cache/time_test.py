from stattest_ext.src.tests_generators.stat_gen_goodness_test import StatGenGoodnessOfFitTest
from stattest_ext.src.time_cache.time_cache import TimeCacheService


# TODO: extend support to AbstractTest later?
class TimeTestHandler:
    def __init__(self, stat_gen: StatGenGoodnessOfFitTest, time_cache=TimeCacheService()):
        self.generator = stat_gen
        self.time_cache = time_cache

    def test_with_time_counting(self, rvs, alpha):  # TODO: count generator.test()??
        rvs_len = len(rvs)

        x_cr = self.generator.calculate_critical_value(rvs_len, alpha)

        start = self.time_cache.count_time()
        statistic = self.generator.execute_statistic(rvs)
        stop = self.time_cache.count_time()

        time = stop - start
        self.time_cache.put_time(self.generator.code(), rvs_len, [time])

        return False if statistic > x_cr else True
