"""Bounded parallel execution with a context created once per worker."""

from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import FIRST_COMPLETED, Executor, Future, ProcessPoolExecutor, ThreadPoolExecutor, wait
from itertools import islice
from multiprocessing import get_context
from threading import local
from types import TracebackType
from typing import Generic, Literal, TypeVar, cast


C = TypeVar("C")
R = TypeVar("R")


class _WorkerState(local):
    context: object


_worker_state = _WorkerState()


def no_context() -> None:
    """Create an empty context for tasks that need no shared worker resources."""
    return None


def _initialize_worker(factory: Callable[[], object]) -> None:
    _worker_state.context = factory()


def _execute_task(task: Callable[[C], R]) -> R:
    return task(cast(C, _worker_state.context))


class Scheduler(Generic[C]):
    """Execute callables receiving a worker-local context and returning any result.

    The factory runs once in each worker started by the pool. In process mode,
    factories, tasks and results must be picklable; the context stays in its
    worker. Contexts should hold reusable clients or session factories, while
    tasks/storage operations manage their own transactions and sessions.

    ``iterate_results`` limits submitted but unconsumed tasks to ``max_pending``
    (default: twice ``max_workers``). Individual ``submit`` calls are unbounded.
    Results arrive as available, without preserving input order. Exceptions
    propagate; cancellation never interrupts tasks that are already running.
    """

    def __init__(
        self,
        max_workers: int,
        context_factory: Callable[[], C],
        *,
        backend: Literal["process", "thread"] = "process",
        max_pending: int | None = None,
    ) -> None:
        for name, value in (("max_workers", max_workers), ("max_pending", max_pending)):
            if name == "max_pending" and value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if backend not in ("process", "thread"):
            raise ValueError("backend must be 'process' or 'thread'")
        self.max_workers = max_workers
        self.max_pending = max_pending if max_pending is not None else 2 * max_workers
        self.context_factory = context_factory
        self.backend = backend
        self._executor: Executor | None = None

    def __enter__(self) -> "Scheduler[C]":
        """Start a pool whose workers own their contexts."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Wait for running tasks; cancel queued work when leaving with an error."""
        self.shutdown(cancel_futures=exc_type is not None)

    def start(self) -> None:
        """Start a fresh pool, rejecting an already running scheduler."""
        if self._executor is not None:
            raise RuntimeError("Scheduler is already running.")
        if self.backend == "process":
            self._executor = ProcessPoolExecutor(
                max_workers=self.max_workers,
                mp_context=get_context("spawn"),
                initializer=_initialize_worker,
                initargs=(self.context_factory,),
            )
        else:
            self._executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                initializer=_initialize_worker,
                initargs=(self.context_factory,),
            )

    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
        """Release the pool, optionally cancelling work that has not started."""
        executor, self._executor = self._executor, None
        if executor is not None:
            executor.shutdown(wait=wait, cancel_futures=cancel_futures)

    def _running_executor(self) -> Executor:
        if self._executor is None:
            raise RuntimeError("Scheduler is not started. Use 'with Scheduler(...) as scheduler:'.")
        return self._executor

    def submit(self, task: Callable[[C], R]) -> Future[R]:
        """Submit one task; its context is supplied by the worker."""
        return self._running_executor().submit(_execute_task, task)

    def iterate_results(self, tasks: Iterable[Callable[[C], R]]) -> Iterator[R]:
        """Lazily execute tasks with bounded buffering and yield ready results.

        Close the iterator when abandoning it early to cancel its pending work.
        Cancellation is best effort; tasks already running may still complete.
        """
        executor = self._running_executor()
        source = iter(tasks)
        pending: set[Future[R]] = set()
        try:
            for task in islice(source, self.max_pending):
                pending.add(executor.submit(_execute_task, task))
            while pending:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    yield future.result()
                    for task in islice(source, 1):
                        pending.add(executor.submit(_execute_task, task))
        finally:
            for future in pending:
                future.cancel()

    def run(self, tasks: Iterable[Callable[[C], R]]) -> list[R]:
        """Collect results in availability order; use iterate_results for streaming."""
        return list(self.iterate_results(tasks))
