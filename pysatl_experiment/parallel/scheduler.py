import psutil
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from typing import Callable, Iterator, Optional


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

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        if not self._active:
            raise RuntimeError("Scheduler not running. Use 'with' or call start().")
        return self._executor.submit(fn, *args, **kwargs)

    def iterate_results(self, tasks: list[Callable[[], any]]) -> Iterator[any]:
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

                        # === МОНИТОРИНГ CPU ===
                        if completed % 5 == 0 or completed == total:
                            cpu_percent = psutil.cpu_percent(interval=0.1)
                            print(f"[MONITOR] {completed}/{total} tasks | CPU: {cpu_percent:.1f}%")
                        # ======================

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

    def run(self, tasks: list[Callable[[], any]]) -> list[any]:
        return list(self.iterate_results(tasks))
