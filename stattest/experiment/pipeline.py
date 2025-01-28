from multiprocessing import Event, Manager, Process, Queue

from tqdm import tqdm


def __show_prog(queue: Queue, shutdown_event, total):
    prog = tqdm(total=total, desc="Processing data", unit_scale=True)
    while not (shutdown_event.is_set() and queue.empty()):
        try:
            to_add = queue.get(timeout=1)
            prog.update(to_add)
            if prog.n >= total:
                break
        except:  # noqa: E722, S110
            pass
    prog.update(total - prog.n)


def start_pipeline(fill_queue, process_entries, num_workers, **kwargs):
    queue_manager = Manager()
    queue = queue_manager.Queue(maxsize=2000)
    info_queue = queue_manager.Queue(maxsize=2000)
    shutdown_event = Event()
    info_shutdown_event = Event()

    total_count = fill_queue(queue, shutdown_event, **kwargs)

    processes = []
    for p in range(num_workers):
        p = Process(
            target=process_entries,
            args=(queue, info_queue, shutdown_event, info_shutdown_event, kwargs),
        )
        p.start()
        processes.append(p)

    if total_count > 0:
        progress = Process(target=__show_prog, args=(info_queue, info_shutdown_event, total_count))
        progress.start()
        progress.join()

    for p in processes:
        p.join()
