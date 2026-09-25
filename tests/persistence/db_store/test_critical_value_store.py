"""Tests for the SQLAlchemy critical value storage implementation."""

from __future__ import annotations

import pytest

from pysatl_experiment.persistence.db_store.critical_value_store import (
    CriticalValue,
    CriticalValueDbStore,
    Distribution,
)


CRITICAL_VALUE_CASES = [
    pytest.param("KS", 10, 0.05, 1.5, id="ks-small"),
    pytest.param("AD", 100, 0.01, 3.25, id="ad-large-sample"),
    pytest.param("KS", 50, 0.1, -0.75, id="negative-value"),
]

TWO_SIDED_CASES = [
    pytest.param("KS", 20, 0.05, (-1.0, 1.0), id="symmetric"),
    pytest.param("AD", 30, 0.01, (-2.5, 4.75), id="asymmetric"),
]

DISTRIBUTION_CASES = [
    pytest.param("KS", 10, [0.1, 0.2, 0.3], id="floats"),
    pytest.param("AD", 5, [1, 2, 3], id="ints-cast-to-float"),
    pytest.param("KS", 7, [0.5], id="single-value"),
]


@pytest.fixture()
def store() -> CriticalValueDbStore:
    """Create an initialized in-memory critical value store."""
    store = CriticalValueDbStore(db_url="sqlite://")
    store.init()
    return store


# Checks that the ORM models are mapped to the expected tables.
def test_orm_models_table_names() -> None:
    assert Distribution.__tablename__ == "distribution"
    assert CriticalValue.__tablename__ == "critical_value"


# Checks that single-sided critical values are stored and read back unchanged.
@pytest.mark.parametrize(("code", "size", "sl", "value"), CRITICAL_VALUE_CASES)
def test_insert_and_get_critical_value(
    store: CriticalValueDbStore, code: str, size: int, sl: float, value: float
) -> None:
    store.insert_critical_value(code, size, sl, value)

    assert store.get_critical_value(code, size, sl) == value


# Checks that two-sided critical values are stored as lower/upper pairs.
@pytest.mark.parametrize(("code", "size", "sl", "value"), TWO_SIDED_CASES)
def test_insert_and_get_two_sided_critical_value(
    store: CriticalValueDbStore, code: str, size: int, sl: float, value: tuple[float, float]
) -> None:
    store.insert_critical_value(code, size, sl, value)

    assert store.get_critical_value(code, size, sl) == value


# Checks that a missing critical value resolves to None.
@pytest.mark.parametrize(
    ("code", "size", "sl"),
    [
        pytest.param("KS", 10, 0.05, id="unknown-code"),
        pytest.param("KNOWN", 999, 0.05, id="unknown-size"),
        pytest.param("KNOWN", 10, 0.5, id="unknown-significance-level"),
    ],
)
def test_get_critical_value_missing_returns_none(store: CriticalValueDbStore, code: str, size: int, sl: float) -> None:
    store.insert_critical_value("KNOWN", 10, 0.05, 2.0)

    assert store.get_critical_value(code, size, sl) is None


# Checks that the sample size is cast to int before being stored.
def test_insert_critical_value_casts_size_to_int(store: CriticalValueDbStore) -> None:
    store.insert_critical_value("KS", 10.9, 0.05, 1.0)  # type: ignore[arg-type]

    assert store.get_critical_value("KS", 10, 0.05) == 1.0


# Checks that inserting a duplicate primary key is rolled back and keeps the first value.
def test_insert_critical_value_duplicate_keeps_first_value(store: CriticalValueDbStore) -> None:
    store.insert_critical_value("KS", 10, 0.05, 1.5)

    store.insert_critical_value("KS", 10, 0.05, 9.9)

    assert store.get_critical_value("KS", 10, 0.05) == 1.5


# Checks that the session stays usable after a rolled back duplicate insert.
def test_session_usable_after_duplicate_critical_value(store: CriticalValueDbStore) -> None:
    store.insert_critical_value("KS", 10, 0.05, 1.5)
    store.insert_critical_value("KS", 10, 0.05, 9.9)

    store.insert_critical_value("AD", 10, 0.05, 2.5)

    assert store.get_critical_value("AD", 10, 0.05) == 2.5
    assert store.get_critical_value("KS", 10, 0.05) == 1.5


# Checks that distributions are serialized and deserialized as float lists.
@pytest.mark.parametrize(("code", "size", "data"), DISTRIBUTION_CASES)
def test_insert_and_get_distribution(store: CriticalValueDbStore, code: str, size: int, data: list[float]) -> None:
    store.insert_distribution(code, size, data)

    assert store.get_distribution(code, size) == [float(value) for value in data]


# Checks that a missing distribution resolves to None.
@pytest.mark.parametrize(
    ("code", "size"),
    [
        pytest.param("MISSING", 10, id="unknown-code"),
        pytest.param("KNOWN", 999, id="unknown-size"),
    ],
)
def test_get_distribution_missing_returns_none(store: CriticalValueDbStore, code: str, size: int) -> None:
    store.insert_distribution("KNOWN", 10, [1.0])

    assert store.get_distribution(code, size) is None


# Checks that a duplicate distribution insert is rolled back and keeps the first data.
def test_insert_distribution_duplicate_keeps_first_data(store: CriticalValueDbStore) -> None:
    store.insert_distribution("KS", 10, [1.0, 2.0])

    store.insert_distribution("KS", 10, [3.0, 4.0])

    assert store.get_distribution("KS", 10) == [1.0, 2.0]


# Checks that distributions of different sizes are stored independently.
def test_distributions_of_different_sizes_are_independent(store: CriticalValueDbStore) -> None:
    store.insert_distribution("KS", 10, [1.0, 2.0])
    store.insert_distribution("KS", 20, [3.0])

    assert store.get_distribution("KS", 10) == [1.0, 2.0]
    assert store.get_distribution("KS", 20) == [3.0]
