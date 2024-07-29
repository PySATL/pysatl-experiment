import multiprocessing
from itertools import repeat

import numpy as np

from stattest.src._ext_package.execution.cache import ThreadSafeCacheResultService
from stattest.src.cr_tests.caches.cache import ThreadSafeMonteCarloCacheService
from stattest.src.cr_tests.criteria.exponentiality_tests import ExponentialityTest, AHSTestExp, RSTestExp, KSTestExp
from stattest.src.cr_tests._tests.generator import NormRVSGenerator

sizes = [30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

norm = [NormRVSGenerator(mean=0, var=1), NormRVSGenerator(mean=-1, var=1), NormRVSGenerator(mean=1, var=1),
        NormRVSGenerator(mean=0, var=2), NormRVSGenerator(mean=0, var=0.5), NormRVSGenerator(mean=2, var=2),
        NormRVSGenerator(mean=-4, var=1), NormRVSGenerator(mean=4, var=1), NormRVSGenerator(mean=0, var=4),
        NormRVSGenerator(mean=0, var=0.1), NormRVSGenerator(mean=-4, var=0.1)]


def run(tests_to_run: [ExponentialityTest], sizes):
    for test in tests_to_run:
        for size in sizes:
            print('Calculating...', test.code(), size)
            test.calculate_critical_value(size, 0.05, 1000)
            print('Critical value calculated', test.code(), size)


if __name__ == '__main__':

    cpu_count = 2  # multiprocessing.cpu_count()

    '''
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    #powers = read_json("result/result.json")
    power_dict = manager.dict()
    caches = ThreadSafeCacheResultService(caches=power_dict, lock=lock)
    alpha = [0.05, 0.1, 0.01]
    tests = [cls() for cls in ExponentialityTest.__subclasses__()]
    tests_chunks = np.array_split(np.array(tests), cpu_count)

    with multiprocessing.Pool(cpu_count) as pool:
        pool.starmap(execute_powers, zip(tests_chunks, repeat(alpha), repeat(True), repeat(caches)))
    '''

    '''
    report_generator = ReportGenerator(
        [PowerTableReportBlockGenerator()])
    report_generator.generate()
    '''


    manager = multiprocessing.Manager()
    lock = manager.Lock()
    cr_dict = manager.dict()
    cache = ThreadSafeMonteCarloCacheService(lock=lock, cache=cr_dict)
    tests = [AHSTestExp(), RSTestExp()]
    #tests = [cls(caches) for cls in ExponentialityTest.__subclasses__()]
    tests_chunks = np.array_split(np.array(tests), cpu_count)
    with multiprocessing.Pool(cpu_count) as pool:
        pool.starmap(run, zip(tests_chunks, repeat(sizes)))


    '''
    rvs_generators = norm
    print('RVS generators count: ', len(rvs_generators))
    sizes_chunks = np.array_split(np.array(sizes), cpu_count)
    start = timeit.default_timer()
    with multiprocessing.Pool(cpu_count) as pool:
        pool.starmap(prepare_rvs_data, zip(repeat(rvs_generators), sizes_chunks))
    # prepare_rvs_data(rvs_generators, sizes)
    stop = timeit.default_timer()
    print('Time: ', stop - start)
    '''
