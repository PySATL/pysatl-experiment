import logging
import multiprocessing
from itertools import repeat
from multiprocessing import RLock, freeze_support

import numpy as np
from tqdm import tqdm

from stattest.experiment.configuration.configuration import AlternativeConfiguration
from stattest.experiment.generator import AbstractRVSGenerator
from stattest.persistence.models import IRvsStore


logger = logging.getLogger(__name__)


def generate_rvs_data(rvs_generator: AbstractRVSGenerator, size, count):
    """
    Generate data rvs

    :param rvs_generator: generator to generate rvs data
    :param size: size of rvs vector
    :param count: rvs count
    :return: Data Frame, where rows is rvs
    """

    return [rvs_generator.generate(size) for i in range(count)]


def prepare_one_size_rvs_data(
    rvs_generators: [AbstractRVSGenerator], size, count, store: IRvsStore, pbar=None
):
    """
    Generate data rvs and save it to store.

    :param size: size of rvs
    :param store: store to persist data
    :param rvs_generators: generators list to generate rvs data
    :param count: rvs count
    """

    for generator in rvs_generators:
        code = generator.code()
        data_count = store.get_rvs_count(code, size)
        if data_count < count:
            count = count - data_count
            data = generate_rvs_data(generator, size, count)
            store.insert_all_rvs(code, size, data)
        if pbar:
            pbar.update(1)


def prepare_rvs_data(
    rvs_generators: [AbstractRVSGenerator],
    sizes,
    count,
    store: IRvsStore,
    thread_count: int = 0,
):
    """
    Generate data rvs and save it to store.

    :param rvs_generators: generators list to generate rvs data
    :param sizes: sizes of rvs
    :param store: store to persist data
    :param count: rvs count
    """

    store.init()

    text = f"#{thread_count}"
    pbar = tqdm(total=len(sizes) * len(rvs_generators), desc=text, position=thread_count)
    for size in sizes:
        prepare_one_size_rvs_data(rvs_generators, size, count, store, pbar)
    pbar.close()


def data_generation_step(alternative_configuration: AlternativeConfiguration, store: IRvsStore):
    """

    Generate data and save it to store.

    :param alternative_configuration: alternative configuration
    :param store: RVS store
    """

    # Skip step
    if alternative_configuration.skip_step:
        logger.info("Skip data generation step")
        return

    logger.info("Start data generation step")
    # Execute before all listeners
    for listener in alternative_configuration.listeners:
        listener.before()

    # Clear all data
    if alternative_configuration.clear_before:
        store.clear_all_rvs()

    threads_count = alternative_configuration.threads
    rvs_generators = alternative_configuration.alternatives
    sizes = alternative_configuration.sizes

    if threads_count > 1:
        sizes_chunks = np.array_split(sizes, threads_count)
        count = len(sizes_chunks) * [alternative_configuration.count]
        store_chunks = len(sizes_chunks) * [store]
        threads_counts = list(range(threads_count))

        freeze_support()  # for Windows support
        tqdm.set_lock(RLock())  # for managing output contention
        with multiprocessing.Pool(
            threads_count, initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),)
        ) as pool:
            pool.starmap(
                prepare_rvs_data,
                zip(
                    repeat(rvs_generators),
                    sizes_chunks,
                    count,
                    store_chunks,
                    threads_counts,
                ),
            )
    else:
        prepare_rvs_data(rvs_generators, sizes, alternative_configuration.count, store)

    # Execute after all listeners
    for listener in alternative_configuration.listeners:
        listener.after()

    logger.info("End data generation step")
