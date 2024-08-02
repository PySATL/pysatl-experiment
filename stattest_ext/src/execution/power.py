from stattest_ext.src.time_cache.time_test import TimeTestHandler
from stattest_std.src.stat_tests.abstract_test import AbstractTest

from stattest_ext.src.execution.generator import AbstractRVSGenerator


# TODO: fix time_test && abstract_test usages!!

def calculate_mean_test_power(test: AbstractTest, rvs_generators: [AbstractRVSGenerator], alpha=0.05, rvs_size=15,
                              count=1_000_000):
    k = 0
    for generator in rvs_generators:
        power = calculate_test_power(test, generator, alpha=alpha, rvs_size=rvs_size, count=count)
        print('power', power)
        k = k + power
    return k / len(rvs_generators)


def calculate_test_power(test: AbstractTest, rvs_generator: AbstractRVSGenerator, alpha=0.05, rvs_size=15,
                         count=1_000_000):
    """
    Calculate statistic test power.

    :param test: statistic test
    :param rvs_generator: rvs generator of alternative hypothesis
    :param alpha: significant level
    :param rvs_size: size of rvs vector
    :param count: count of test execution
    :return:
    """

    k = 0
    for i in range(count):
        rvs = rvs_generator.generate(rvs_size)
        x = test.test(rvs, alpha=alpha)
        if x is False:
            k = k + 1
    return k / count


def calculate_power(test: TimeTestHandler, data: [[float]], alpha=0.05, calculate_time=False) -> float:
    """
    Calculate statistic test power.

    :param test: statistic test
    :param data: rvs data of alternative hypothesis
    :param alpha: significant level
    :param calculate_time: counting time flag
    :return: statistic test power
    """
    k = 0
    count = len(data[0])
    for i in range(count):
        if calculate_time:
            x = test.test_with_time_counting(data[i], alpha=alpha)
        else:
            x = test.generator.test(data[i], alpha=alpha)

        if x is False:
            k = k + 1
    return k / count


def calculate_powers(tests: [AbstractTest], data: [[float]], alpha=0.05, calculate_time=False) -> [float]:
    """
    Calculate statistic tests power.

    :param tests: statistic tests
    :param data: rvs data of alternative hypothesis
    :param alpha: significant level
    :param calculate_time: counting time flag
    :return: statistic test power
    """

    return [calculate_power(test, data, alpha, calculate_time) for test in tests]
