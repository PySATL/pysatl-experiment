"""Tests for the abstract experiment step interface."""

from __future__ import annotations

import pytest

from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep


class StubExperimentStep(IExperimentStep):
    """Concrete step delegating to the abstract base implementation."""

    def run(self) -> None:
        """Delegate to the abstract base implementation."""
        IExperimentStep.run(self)


# Checks that the abstract base class itself cannot be instantiated.
def test_abstract_step_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        IExperimentStep()  # type: ignore[abstract]


# Checks that the base class declares exactly one abstract method.
def test_abstract_step_declares_single_abstract_method() -> None:
    assert IExperimentStep.__abstractmethods__ == frozenset({"run"})


# Checks that the abstract run body raises NotImplementedError.
def test_abstract_step_run_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        StubExperimentStep().run()


# Checks that a subclass overriding run can execute normally.
def test_subclass_can_override_run() -> None:
    class ConcreteStep(IExperimentStep):
        """Step that records its execution instead of delegating."""

        def __init__(self) -> None:
            self.calls = 0

        def run(self) -> None:
            """Record a single execution."""
            self.calls += 1

    step = ConcreteStep()
    step.run()

    assert step.calls == 1


# Checks that the abstract run body is callable on any subclass instance.
def test_abstract_run_body_is_callable_on_stub() -> None:
    with pytest.raises(NotImplementedError):
        IExperimentStep.run(StubExperimentStep())
