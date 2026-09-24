"""Tests for the abstract report builder interface."""

import inspect
from abc import ABC

import pytest

from pysatl_experiment.experiment_execution.step.report_step.abstract_report_builder import IReportBuilder


class RecordingReportBuilder(IReportBuilder):
    """Concrete builder that records every build invocation."""

    def __init__(self) -> None:
        self.build_calls = 0

    def build(self) -> None:
        """Record a single build invocation."""
        self.build_calls += 1


class SuperCallingReportBuilder(IReportBuilder):
    """Concrete builder that calls the abstract base implementation."""

    def build(self) -> None:
        """Call the base class implementation directly."""
        IReportBuilder.build(self)


class IncompleteReportBuilder(IReportBuilder):
    """Builder that does not implement the required abstract method."""


# Checks that the interface is a proper abstract base class.
def test_interface_is_an_abc() -> None:
    assert issubclass(IReportBuilder, ABC)
    assert inspect.isabstract(IReportBuilder)


# Checks that the interface declares build as its only abstract method.
def test_build_is_the_only_abstract_method() -> None:
    assert IReportBuilder.__abstractmethods__ == frozenset({"build"})


# Checks that the abstract build method is exposed on the interface.
def test_build_method_is_declared_without_arguments() -> None:
    assert callable(IReportBuilder.build)
    assert list(inspect.signature(IReportBuilder.build).parameters) == ["self"]


# Checks that the interface itself cannot be instantiated.
def test_interface_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError, match="build"):
        IReportBuilder()  # type: ignore[abstract]


# Checks that a subclass without build cannot be instantiated either.
def test_incomplete_subclass_cannot_be_instantiated() -> None:
    assert inspect.isabstract(IncompleteReportBuilder)

    with pytest.raises(TypeError, match="build"):
        IncompleteReportBuilder()  # type: ignore[abstract]


# Checks that a complete subclass can be instantiated and used.
def test_concrete_subclass_can_be_instantiated() -> None:
    builder = RecordingReportBuilder()

    assert isinstance(builder, IReportBuilder)
    assert builder.build_calls == 0


# Checks that calling build on a concrete subclass is allowed and returns None.
def test_concrete_build_returns_none() -> None:
    builder = RecordingReportBuilder()

    assert builder.build() is None  # type: ignore[func-returns-value]
    assert builder.build_calls == 1


# Checks that build can be invoked repeatedly.
def test_concrete_build_can_be_called_multiple_times() -> None:
    builder = RecordingReportBuilder()

    builder.build()
    builder.build()

    assert builder.build_calls == 2


# Checks that the base implementation is callable and does nothing.
def test_base_build_implementation_is_callable() -> None:
    builder = SuperCallingReportBuilder()

    assert builder.build() is None  # type: ignore[func-returns-value]
