import logging
from multiprocessing import Queue, Manager, Event, Process

from tqdm import tqdm

from stattest.experiment.configuration.configuration import TestConfiguration, TestWorker
from stattest.experiment.pipeline import start_pipeline
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

def process_entries(generate_queue: Queue, info_queue: Queue, generate_shutdown_event: Event,
                    info_shutdown_event: Event, kwargs):
    worker = kwargs['worker']
    worker.init()

    while not (generate_shutdown_event.is_set() and generate_queue.empty()):
        if not generate_queue.empty():
            test, data, code, size = generate_queue.get()
            result = worker.execute(test, data, code, size)
            worker.save_result(result)
            info_queue.put(1)

    info_shutdown_event.set()

def fill_queue(queue, generate_shutdown_event, tests: [AbstractTestStatistic]=None, store=None, **kwargs):
    stat = store.get_rvs_stat()

    for code, size, _ in stat:
        data = store.get_rvs(code, size)
        for test in tests:
            queue.put((test, data, code, size))

    generate_shutdown_event.set()

    return len(stat) * len(tests)


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

    start_pipeline(fill_queue, process_entries, threads_count, worker=worker, tests=tests, store=rvs_store)

    # Execute after all listeners
    for listener in configuration.listeners:
        listener.after()

    logger.info("End test step")
