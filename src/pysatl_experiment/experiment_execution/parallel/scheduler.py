"""Parallel task scheduling utilities."""

import logging
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from multiprocessing.context import BaseContext
from typing import Any

from pysatl_experiment.configuration.models.task_failure_policy import TaskFailurePolicy


logger = logging.getLogger(__name__)


@dataclass
class TaskFailure:
    """
    Record of a single failed task.

    Attributes
    ----------
    index : int
        Position of the failed task in the submitted task sequence.
    error : Exception
        Exception raised by the task.
    """

    index: int
    error: Exception


class TaskFailuresExceededError(RuntimeError):
    """Raised when the share of failed tasks exceeds the configured threshold."""


class Scheduler:
    """
    Runtime task scheduler based on ProcessPoolExecutor.

    Parameters
    ----------
    max_workers : int
        Maximum number of parallel worker processes.
    worker_initializer : Callable | None, optional
        Initializer run once in each worker process at startup
        (e.g. ``configure_worker_logging``).
    worker_initargs : tuple, default=()
        Arguments passed to ``worker_initializer``.
    mp_context : multiprocessing.context.BaseContext | None, optional
        Multiprocessing context for the executor (e.g. ``spawn``).
        When worker logging is used, the same context must be passed
        to ``WorkerLogListener``. Defaults to the platform default.
    """

    def __init__(
        self,
        max_workers: int,
        worker_initializer: Callable | None = None,
        worker_initargs: tuple = (),
        mp_context: BaseContext | None = None,
    ) -> None:
        """
        Initialize scheduler.

        Parameters
        ----------
        max_workers : int
            Maximum number of parallel worker processes.
        worker_initializer : Callable | None, optional
            Initializer run once in each worker process at startup.
        worker_initargs : tuple, default=()
            Arguments passed to ``worker_initializer``.
        mp_context : multiprocessing.context.BaseContext | None, optional
            Multiprocessing context for the executor; defaults to the
            platform default context.
        """
        self.max_workers = max_workers
        self._worker_initializer = worker_initializer
        self._worker_initargs = worker_initargs
        self._mp_context = mp_context
        self._executor: ProcessPoolExecutor | None = None
        self._active = False
        self.failures: list[TaskFailure] = []

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

        self._executor = ProcessPoolExecutor(
            max_workers=self.max_workers,
            mp_context=self._mp_context,
            initializer=self._worker_initializer,
            initargs=self._worker_initargs,
        )
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

    def iterate_results(
        self,
        tasks: Sequence[Callable[[], Any]],
        failure_policy: TaskFailurePolicy = TaskFailurePolicy.FAIL_FAST,
        failure_threshold: float = 0.01,
    ) -> Iterator[Any]:
        """
        Execute tasks and yield results as they complete.

        Parameters
        ----------
        tasks : Sequence[Callable[[], Any]]
            Tasks to execute.
        failure_policy : TaskFailurePolicy, default=TaskFailurePolicy.FAIL_FAST
            ``FAIL_FAST`` re-raises the first task exception and aborts
            the iteration. ``ISOLATE`` logs the exception, records it in
            ``self.failures`` and continues with the remaining tasks.
        failure_threshold : float, default=0.01
            Maximum allowed share of failed tasks under the ``ISOLATE``
            policy. When the observed share is higher, the remaining
            results are still drained and ``TaskFailuresExceededError``
            is raised after the iteration completes.

        Yields
        ------
        Any
            Task execution results.

        Raises
        ------
        ValueError
            If ``failure_threshold`` is outside the [0, 1] range.
        TaskFailuresExceededError
            If the share of failed tasks exceeds ``failure_threshold``
            under the ``ISOLATE`` policy.
        """
        if not 0.0 <= failure_threshold <= 1.0:
            raise ValueError("failure_threshold must be in the [0, 1] range.")

        if not self._active:
            raise RuntimeError("Use inside 'with' block.")

        task_iter = iter(tasks)
        futures: dict[Future, int] = {}
        total = len(tasks)
        submitted = 0
        self.failures = []

        for _ in range(min(self.max_workers, total)):
            try:
                task = next(task_iter)
            except StopIteration:
                break
            futures[self.submit(task)] = submitted
            submitted += 1

        while futures:
            for future in as_completed(futures):
                index = futures.pop(future)
                try:
                    yield future.result()
                except Exception as exc:
                    if failure_policy is TaskFailurePolicy.FAIL_FAST:
                        raise
                    logger.exception("Task %s failed; continuing with remaining tasks.", index)
                    self.failures.append(TaskFailure(index=index, error=exc))

                try:
                    next_task = next(task_iter)
                except StopIteration:
                    continue
                futures[self.submit(next_task)] = submitted
                submitted += 1

        failed_count = len(self.failures)
        if failed_count and failed_count / total > failure_threshold:
            raise TaskFailuresExceededError(
                f"{failed_count} of {total} tasks failed ({failed_count / total:.2%}), "
                f"which exceeds the configured threshold ({failure_threshold:.2%})."
            )

    def run(
        self,
        tasks: Sequence[Callable[[], Any]],
        failure_policy: TaskFailurePolicy = TaskFailurePolicy.FAIL_FAST,
        failure_threshold: float = 0.01,
    ) -> list[Any]:
        """
        Execute all tasks and collect results.

        Parameters
        ----------
        tasks : Sequence[Callable[[], Any]]
            Tasks to execute.
        failure_policy : TaskFailurePolicy, default=TaskFailurePolicy.FAIL_FAST
            Policy for handling individual task failures.
        failure_threshold : float, default=0.01
            Maximum allowed share of failed tasks under the ``ISOLATE`` policy.

        Returns
        -------
        list[Any]
            Task execution results.
        """
        return list(self.iterate_results(tasks, failure_policy=failure_policy, failure_threshold=failure_threshold))
