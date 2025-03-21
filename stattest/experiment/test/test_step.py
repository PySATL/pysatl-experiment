import logging
from collections.abc import Sequence
from multiprocessing import Queue
from multiprocessing.synchronize import Event as EventClass

from pysatl.criterion import AbstractStatistic
from tqdm import tqdm

from stattest.experiment.configuration.configuration import TestConfiguration, TestWorker
from stattest.experiment.pipeline import start_pipeline
from stattest.persistence import IRvsStore
from stattest.persistence.models import IResultStore


logger = logging.getLogger(__name__)


def execute_tests(
    worker: TestWorker,
    tests: list[AbstractStatistic],
    rvs_store: IRvsStore,
    result_store: IResultStore,
    thread_count: int = 0,
):
    rvs_store.init()
    result_store.init()
    worker.init()

    stat = rvs_store.get_rvs_stat()
    text = f"#{thread_count}"
    pbar = tqdm(total=len(stat) * len(tests), desc=text, position=thread_count)
    for code, size, _ in stat:
        data = rvs_store.get_rvs(code, size)
        for test in tests:
            result_id = worker.build_id(test, data, code, size)
            result = result_store.get_result(result_id)
            if result is None:
                result = worker.execute(test, data, code, size)
                result_store.insert_result(result_id, result)
            pbar.update(1)


def process_entries(
    generate_queue: Queue,
    info_queue: Queue,
    generate_shutdown_event: EventClass,
    info_shutdown_event: EventClass,
    kwargs,
):
    worker: TestWorker = kwargs["worker"]
    result_store: IResultStore = kwargs["result_store"]
    worker.init()

    while not (generate_shutdown_event.is_set() and generate_queue.empty()):
        if not generate_queue.empty():
            test, data, code, size = generate_queue.get()
            result_id = worker.build_id(test, data, code, size)
            result = result_store.get_result(result_id)

            if result is None:
                result = worker.execute(test, data, code, size)
                result_store.insert_result(result_id, result)

            info_queue.put(1)

    info_shutdown_event.set()


def fill_queue(queue, generate_shutdown_event, kwargs):
    tests: list[AbstractStatistic] = kwargs["tests"]
    store: IRvsStore = kwargs["store"]

    store.init()
    stat = store.get_rvs_stat()

    for code, size, _ in stat:
        data = store.get_rvs(code, size)
        for test in tests:
            queue.put((test, data, code, size))

    generate_shutdown_event.set()

    return len(stat) * len(tests)


def get_total_count(tests: Sequence[AbstractStatistic], store: IRvsStore):
    store.init()
    stat = store.get_rvs_stat()
    return len(stat) * len(tests)


def execute_test_step(
    configuration: TestConfiguration, rvs_store: IRvsStore, result_store: IResultStore
):
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

    start_pipeline(
        fill_queue,
        process_entries,
        threads_count,
        total_count=get_total_count(tests, rvs_store),
        queue_size=10,
        worker=worker,
        tests=tests,
        store=rvs_store,
        result_store=result_store,
    )

    # Execute after all listeners
    for listener in configuration.listeners:
        listener.after()

    logger.info("End test step")
