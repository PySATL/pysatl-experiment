from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Callable, Optional


class Scheduler:
    """
    Runtime task scheduler based on ProcessPoolExecutor.
    """

    def __init__(self, max_workers: int):
        self.max_workers = max_workers
        self._executor: Optional[ProcessPoolExecutor] = None
        self._active = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def start(self):
        if self._active:
            raise RuntimeError("Scheduler is already running")
        self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        self._active = True

    def shutdown(self, wait: bool = True):
        if self._executor and self._active:
            self._executor.shutdown(wait=wait)
            self._active = False

    def submit(self, fn: Callable, *args, **kwargs) -> Any:
        if self._executor is None:
            raise RuntimeError("Scheduler is not started. Use 'with Scheduler() as scheduler:'")
        return self._executor.submit(fn, *args, **kwargs)

    def iterate_results(self, tasks: list[Callable[[], Any]]) -> Iterator[Any]:
        if not self._active:
            raise RuntimeError("Use inside 'with' block")

        task_iter = iter(tasks)
        futures = {}
        total = len(tasks)
        completed = 0

        for _ in range(min(self.max_workers, total)):
            try:
                task = next(task_iter)
                futures[self.submit(task)] = task
            except StopIteration:
                break

        while futures:
            try:
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        completed += 1
                        yield result

                        try:
                            next_task = next(task_iter)
                            futures[self.submit(next_task)] = next_task
                        except StopIteration:
                            pass

                    except Exception as e:
                        raise e

                    finally:
                        del futures[future]

            except TimeoutError:
                continue

    def run(self, tasks: list[Callable[[], Any]]) -> list[Any]:
        return list(self.iterate_results(tasks))
