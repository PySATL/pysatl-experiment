"""Tests for the generic storage interfaces of the experiment system."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from pysatl_experiment.persistence.interfaces import ICriticalValueStore, IResultStore, IRvsStore, IStore


class StubRvsStore(IRvsStore):
    """In-memory random values store recording every inserted sample."""

    def __init__(self) -> None:
        self.inserted: list[tuple[str, int, list[float]]] = []

    def insert_rvs(self, generator_code: str, size: int, data: list[float]) -> None:
        """Record a single inserted sample."""
        self.inserted.append((generator_code, size, list(data)))

    def get_rvs(self, generator_code: str, size: int) -> list[list[float]]:
        """Return every recorded sample payload."""
        return [row[2] for row in self.inserted]

    def get_rvs_stat(self) -> list[tuple[str, int, int]]:
        """Return no aggregated statistics."""
        return []

    def clear_all_rvs(self) -> None:
        """Drop every recorded sample."""
        self.inserted.clear()


# Checks that the base store lifecycle hooks are no-ops.
def test_base_store_lifecycle_hooks_return_none() -> None:
    store = IStore()

    assert store.migrate() is None
    assert store.init() is None


# Checks that bulk insertion delegates every sample to insert_rvs.
def test_insert_all_rvs_delegates_each_sample() -> None:
    store = StubRvsStore()

    IRvsStore.insert_all_rvs(store, "NORM", 3, [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])

    assert store.inserted == [("NORM", 3, [1.0, 2.0, 3.0]), ("NORM", 3, [4.0, 5.0, 6.0])]


# Checks that bulk insertion of an empty collection stores nothing.
def test_insert_all_rvs_with_empty_data_is_noop() -> None:
    store = StubRvsStore()

    IRvsStore.insert_all_rvs(store, "NORM", 3, [])

    assert store.inserted == []


# Checks that the sample count is derived from the stored payload length.
@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        pytest.param([], 0, id="empty"),
        pytest.param([[1.0], [2.0]], 2, id="two-samples"),
        pytest.param([[1.0]] * 5, 5, id="five-samples"),
    ],
)
def test_get_rvs_count_counts_stored_samples(payload: list[list[float]], expected: int) -> None:
    store = StubRvsStore()

    IRvsStore.insert_all_rvs(store, "NORM", 1, payload)

    assert store.get_rvs_count("NORM", 1) == expected


# Checks that the abstract random values bodies are reachable through the base class.
@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        pytest.param("insert_rvs", ("NORM", 3, [1.0]), id="insert-rvs"),
        pytest.param("get_rvs", ("NORM", 3), id="get-rvs"),
        pytest.param("get_rvs_stat", (), id="get-rvs-stat"),
        pytest.param("clear_all_rvs", (), id="clear-all-rvs"),
    ],
)
def test_abstract_rvs_bodies_return_none(method_name: str, args: tuple[Any, ...]) -> None:
    assert getattr(IRvsStore, method_name)(MagicMock(), *args) is None


# Checks that the abstract critical value bodies are reachable through the base class.
@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        pytest.param("insert_critical_value", ("KS", 10, 0.05, 1.5), id="insert-critical-value"),
        pytest.param("insert_distribution", ("KS", 10, [0.1, 0.2]), id="insert-distribution"),
        pytest.param("get_critical_value", ("KS", 10, 0.05), id="get-critical-value"),
        pytest.param("get_distribution", ("KS", 10), id="get-distribution"),
    ],
)
def test_abstract_critical_value_bodies_return_none(method_name: str, args: tuple[Any, ...]) -> None:
    assert getattr(ICriticalValueStore, method_name)(MagicMock(), *args) is None


# Checks that the critical value interface declares only the four storage methods.
def test_critical_value_interface_abstract_methods() -> None:
    assert ICriticalValueStore.__abstractmethods__ == frozenset(
        {"insert_critical_value", "insert_distribution", "get_critical_value", "get_distribution"}
    )


# Checks that the random values interface declares the four sample methods.
def test_rvs_interface_abstract_methods() -> None:
    assert IRvsStore.__abstractmethods__ == frozenset({"insert_rvs", "get_rvs", "get_rvs_stat", "clear_all_rvs"})


class StubResultStore(IResultStore):
    """Concrete result store used to exercise the interface bodies."""

    def insert_result(self, result_id: str, result: Any) -> None:
        """Accept a stored result without persisting it."""
        pass

    def get_result(self, result_id: str) -> Any:
        """Return no stored result."""
        return None

    def get_results(self, offset: int, limit: int) -> list[Any]:
        """Return no stored results."""
        return []


# Checks that the result store interface bodies are reachable without an implementation.
@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        pytest.param("insert_result", ("r1", {"a": 1}), id="insert-result"),
        pytest.param("get_result", ("r1",), id="get-result"),
        pytest.param("get_results", (0, 10), id="get-results"),
    ],
)
def test_result_store_bodies_return_none(method_name: str, args: tuple[Any, ...]) -> None:
    assert getattr(IResultStore, method_name)(StubResultStore(), *args) is None


# Checks that the result store interface also inherits the base lifecycle hooks.
def test_result_store_inherits_lifecycle_hooks() -> None:
    store = StubResultStore()

    assert store.migrate() is None
    assert store.init() is None


# Checks that the abstract result store bodies are also reachable as unbound calls.
def test_result_store_abstract_bodies_are_pass() -> None:
    assert IResultStore.insert_result(MagicMock(), "r1", object()) is None
    assert IResultStore.get_result(MagicMock(), "r1") is None
    assert IResultStore.get_results(MagicMock(), 0, 10) is None
