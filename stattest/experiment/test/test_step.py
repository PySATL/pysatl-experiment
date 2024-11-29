import logging
import multiprocessing
from itertools import repeat
from multiprocessing import freeze_support

import numpy as np
from tqdm import tqdm

from stattest.experiment.configuration.configuration import (
    TestConfiguration,
    TestWorker,
)
from stattest.persistence import IRvsStore
from stattest.test import AbstractTestStatistic

logger = logging.getLogger(__name__)


def execute_tests(
    worker: TestWorker,
    tests: [AbstractTestStatistic],
    rvs_store: IRvsStore,
    thread_count: int = 0,
):
    rvs_store.init()
    worker.init()

    stat = rvs_store.get_rvs_stat()
    text = f"#{thread_count}"
    pbar = tqdm(total=len(stat) * len(tests), desc=text, position=thread_count)
    for code, size, _ in stat:
        data = rvs_store.get_rvs(code, size)
        for test in tests:
            result = worker.execute(test, data, code, size)
            worker.save_result(result)
            pbar.update(1)


def execute_test_step(configuration: TestConfiguration, rvs_store: IRvsStore):
    threads_count = configuration.threads
    worker = configuration.worker
    tests = configuration.tests

    # Skip step
    if configuration.skip_step:
        logger.info("Skip test step")
        return

    logger.info("Start test step")

    # Execute before all listeners
    for listener in configuration.listeners:
        listener.before()

    if threads_count > 1:
        freeze_support()  # for Windows support
        tqdm.set_lock(multiprocessing.RLock())  # for managing output contention
        tests_chunks = np.array_split(tests, threads_count)
        threads_counts = list(range(threads_count))
        with multiprocessing.Pool(threads_count) as pool:
            pool.starmap(
                execute_tests,
                zip(repeat(worker), tests_chunks, repeat(rvs_store), threads_counts),
            )
    else:
        execute_tests(worker, tests, rvs_store)

    # Execute after all listeners
    for listener in configuration.listeners:
        listener.after()

    logger.info("End test step")
