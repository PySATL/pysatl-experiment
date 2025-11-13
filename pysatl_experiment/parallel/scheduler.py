import psutil
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from typing import Callable, Iterator, Optional
import multiprocessing as mp


class AdaptiveScheduler:
    """
    Adaptive task scheduler.
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        cpu_target: float = 0.7,
        scale_up_threshold: float = 0.8,
        scale_down_threshold: float = 0.3,
    ):
        self.max_workers = max_workers or min(16, mp.cpu_count())
        self.cpu_target = cpu_target
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self._executor: Optional[ProcessPoolExecutor] = None
        self._active = False
        self._current_workers = min(2, self.max_workers)

    def _should_scale_up(self) -> bool:
        cpu = psutil.cpu_percent(interval=0.1)
        return cpu > self.scale_up_threshold and self._current_workers < self.max_workers

    def _should_scale_down(self) -> bool:
        cpu = psutil.cpu_percent(interval=0.1)
        return cpu < self.scale_down_threshold and self._current_workers > 1

    def _adjust_workers(self):
        if self._should_scale_up():
            self._current_workers = min(self._current_workers + 1, self.max_workers)
        elif self._should_scale_down():
            self._current_workers = max(self._current_workers - 1, 1)

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

        for _ in range(min(self._current_workers, total)):
            try:
                task = next(task_iter)
                futures[self.submit(task)] = task
            except StopIteration:
                break

        while futures:
            self._adjust_workers()

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

                    except Exception:
                        pass

                    finally:
                        del futures[future]

            except TimeoutError:
                continue