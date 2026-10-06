"""Tests for the abstract worker interface and result marker."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from pysatl_experiment.experiment_execution.step.execution_step.abstract_worker import IWorker, WorkerResult


@dataclass
class StubWorkerResult(WorkerResult):
    """Worker result carrying a single string payload."""

    value: str = ""


class StubWorker(IWorker[StubWorkerResult]):
    """Concrete worker delegating to the abstract base implementation."""

    def execute(self) -> StubWorkerResult:
        """Delegate to the abstract base implementation."""
        return IWorker.execute(self)  # type: ignore[return-value]


# Checks that the result marker base class is instantiable without fields.
def test_worker_result_is_instantiable() -> None:
    assert WorkerResult() == WorkerResult()


# Checks that a worker result subclass carries its own fields.
def test_worker_result_subclass_carries_fields() -> None:
    assert StubWorkerResult(value="payload").value == "payload"


# Checks that the abstract base class itself cannot be instantiated.
def test_abstract_worker_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        IWorker()  # type: ignore[abstract]


# Checks that the base class declares exactly one abstract method.
def test_abstract_worker_declares_single_abstract_method() -> None:
    assert IWorker.__abstractmethods__ == frozenset({"execute"})


# Checks that the abstract execute body returns None.
def test_abstract_execute_body_returns_none() -> None:
    assert StubWorker().execute() is None


# Checks that the generic result parameter is bound to the worker class.
def test_worker_is_generic_over_worker_result() -> None:
    assert IWorker[StubWorkerResult] is not None
    assert issubclass(StubWorkerResult, WorkerResult)
