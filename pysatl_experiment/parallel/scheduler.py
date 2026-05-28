"""Parallel task scheduling utilities."""

from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Callable


class Scheduler:
    """
    Runtime task scheduler based on ProcessPoolExecutor.

    Parameters
    ----------
    max_workers : int
        Maximum number of parallel worker processes.
    """

    def __init__(self, max_workers: int) -> None:
        """
        Initialize scheduler.

        Parameters
        ----------
        max_workers : int
            Maximum number of parallel worker processes.
        """
        self.max_workers = max_workers
        self._executor: ProcessPoolExecutor | None = None
        self._active = False

    def __enter__(self) -> "Scheduler":
        """Start scheduler context."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Shutdown scheduler context.

        Parameters
        ----------
        exc_type : type | None
            Exception type.
        exc_val : BaseException | None
            Exception value.
        exc_tb : object | None
            Exception traceback.
        """
        self.shutdown()

    def start(self) -> None:
        """Start executor."""
        if self._active:
            raise RuntimeError("Scheduler is already running.")

        self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        self._active = True

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown executor.

        Parameters
        ----------
        wait : bool, default=True
            Wait until all running tasks are completed.
        """
        if self._executor and self._active:
            self._executor.shutdown(wait=wait)
            self._active = False

    def submit(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Submit task to executor.

        Parameters
        ----------
        fn : Callable
            Task function.

        Returns
        -------
        Any
            Submitted future object.
        """
        if self._executor is None:
            raise RuntimeError("Scheduler is not started. Use 'with Scheduler() as scheduler:'.")

        return self._executor.submit(fn, *args, **kwargs)

    def iterate_results(self, tasks: list[Callable[[], Any]]) -> Iterator[Any]:
        """
        Execute tasks and yield results as they complete.

        Parameters
        ----------
        tasks : list[Callable[[], Any]]
            Tasks to execute.

        Yields
        ------
        Any
            Task execution results.
        """
        if not self._active:
            raise RuntimeError("Use inside 'with' block.")

        task_iter = iter(tasks)
        futures = {}
        total = len(tasks)
        completed = 0  # TODO: not used??

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

                    finally:
                        del futures[future]

            except TimeoutError:  # TODO: ??
                continue

    def run(self, tasks: list[Callable[[], Any]]) -> list[Any]:
        """
        Execute all tasks and collect results.

        Parameters
        ----------
        tasks : list[Callable[[], Any]]
            Tasks to execute.

        Returns
        -------
        list[Any]
            Task execution results.
        """
        return list(self.iterate_results(tasks))
