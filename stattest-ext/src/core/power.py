import pandas as pd

from stattest.src.cr_tests.criteria.abstract_test import AbstractTest
from tqdm import tqdm

from stattest.src.cr_tests._tests.generator import AbstractRVSGenerator


# TODO: relocate to execution in ext_package!

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


def calculate_power(test: AbstractTest, data: [[float]], alpha=0.05, calculate_time=False) -> float:
    """
    Calculate statistic test power.

    :param test: statistic test
    :param data: rvs data of alternative hypothesis
    :param alpha: significant level
    :return: statistic test power
    """
    k = 0
    count = len(data[0])
    for i in range(count):
        x = test.test(data[i], alpha=alpha, calculate_time=calculate_time)
        if x is False:
            k = k + 1
    return k / count


def calculate_powers(tests: [AbstractTest], data: [[float]], alpha=0.05, calculate_time=False) -> [float]:
    """
    Calculate statistic tests power.

    :param tests: statistic tests
    :param data: rvs data of alternative hypothesis
    :param alpha: significant level
    :return: statistic test power
    """

    return [calculate_power(test, data, alpha, calculate_time) for test in tests]
