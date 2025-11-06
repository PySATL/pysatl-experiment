import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from typing import Callable, Any, Iterator, Optional
import psutil


class AdaptiveScheduler:
    """
    Runtime task scheduler with resource awareness and streaming support.
    """

    def __init__(self, max_workers: Optional[int] = None, cpu_limit_percent: float = 80.0):
        self.max_workers = max_workers or min(16, mp.cpu_count())
        self.cpu_limit = cpu_limit_percent
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
        print(f"[Scheduler] Started with {self.max_workers} workers")

    def shutdown(self, wait: bool = True):
        if self._executor and self._active:
            self._executor.shutdown(wait=wait)
            self._active = False
            print("[Scheduler] Shutdown complete")

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        if not self._active:
            raise RuntimeError("Scheduler not running. Use 'with' or call start().")
        return self._executor.submit(fn, *args, **kwargs)

    def run(self, tasks: list[Callable[[], Any]]) -> list[Any]:
        if not self._active:
            with self:
                return self._run_internal(tasks)
        return self._run_internal(tasks)

    def _run_internal(self, tasks: list[Callable[[], Any]]) -> list[Any]:
        futures = [self.submit(task) for task in tasks]
        results = []
        for future in as_completed(futures):
            results.append(future.result())
        return results

    def iterate_results(self, tasks: list[Callable[[], Any]]) -> Iterator[Any]:
        if not self._active:
            raise RuntimeError("Use iterate_results() only inside 'with' block")

        futures = {self.submit(task): i for i, task in enumerate(tasks)}
        total = len(tasks)
        completed = 0

        while futures:
            for future in as_completed(futures):
                result = future.result()
                futures.pop(future)
                completed += 1

                if completed % 5 == 0 or completed == total:
                    cpu = psutil.cpu_percent()
                    print(f"[Scheduler] {completed}/{total} done | CPU: {cpu:.1f}%")

                yield result