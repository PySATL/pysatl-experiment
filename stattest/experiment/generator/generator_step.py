import logging
from multiprocessing import Queue
from multiprocessing.synchronize import Event as EventClass

from stattest.experiment.configuration.configuration import GeneratorConfiguration
from stattest.experiment.generator import AbstractRVSGenerator
from stattest.experiment.pipeline import start_pipeline
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

    return [rvs_generator.generate(size) for _ in range(count)]


def process_entries(
    generate_queue: Queue,
    info_queue: Queue,
    generate_shutdown_event: EventClass,
    info_shutdown_event: EventClass,
    kwargs,
):
    store = kwargs["store"]
    store.init()

    while not (generate_shutdown_event.is_set() and generate_queue.empty()):
        if not generate_queue.empty():
            generator, size, count = generate_queue.get()
            data = generate_rvs_data(generator, size, count)
            store.insert_all_rvs(generator.code(), size, data)
            info_queue.put(1)

    info_shutdown_event.set()


def fill_queue(
    queue,
    generate_shutdown_event,
    kwargs,
):
    sizes = kwargs["sizes"]
    count = kwargs["count"]
    store: IRvsStore = kwargs["store"]
    rvs_generators: list[AbstractRVSGenerator] | None = kwargs["rvs_generators"]

    store.init()

    for size in sizes:
        for generator in rvs_generators:
            try:
                code = generator.code()
                data_count = store.get_rvs_count(code, size)
                if data_count < count:
                    count = count - data_count
                    queue.put((generator, size, count))
            except Exception as e:
                logger.warning(f"Error on generation ${generator.code()} with size ${size}", e)

    generate_shutdown_event.set()


def data_generation_step(alternative_configuration: GeneratorConfiguration, store: IRvsStore):
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

    start_pipeline(
        fill_queue,
        process_entries,
        threads_count,
        total_count=len(sizes) * len(rvs_generators),
        queue_size=2000,
        sizes=sizes,
        count=alternative_configuration.count,
        rvs_generators=rvs_generators,
        store=store,
    )

    # Execute after all listeners
    for listener in alternative_configuration.listeners:
        listener.after()

    logger.info("End data generation step")
