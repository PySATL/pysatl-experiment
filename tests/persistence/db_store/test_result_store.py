"""Tests for the SQLAlchemy result storage implementation."""

from __future__ import annotations

import pytest

from pysatl_experiment.persistence.db_store.result_store import ResultDbStore, ResultModel
from pysatl_experiment.persistence.models.random_values import RandomValuesModel


def make_result(sample_size: int = 3, experiment_name: str = "1") -> RandomValuesModel:
    """Build a JSON-serializable result payload backed by a real importable model."""
    return RandomValuesModel(
        generator_code="NORM",
        generator_parameters=[0.0, 1.0],
        sample_size=sample_size,
        experiment_name=experiment_name,
        data=[float(index) for index in range(sample_size)],
    )


@pytest.fixture()
def store() -> ResultDbStore:
    """Create an initialized in-memory result store."""
    store = ResultDbStore(db_url="sqlite://")
    store.init()
    return store


# Checks that the ORM model is mapped to the expected table.
def test_result_model_table_name() -> None:
    assert ResultModel.__tablename__ == "result"


# Checks that a stored result is deserialized back into an equal object.
def test_insert_and_get_result_round_trips(store: ResultDbStore) -> None:
    result = make_result()

    store.insert_result("r1", result)

    restored = store.get_result("r1")
    assert isinstance(restored, RandomValuesModel)
    assert restored == result


# Checks that results of different sample sizes keep independent payloads.
@pytest.mark.parametrize("sample_size", [1, 3, 8])
def test_results_with_different_sample_sizes_stay_independent(store: ResultDbStore, sample_size: int) -> None:
    result = make_result(sample_size=sample_size)
    store.insert_result(f"r{sample_size}", result)

    assert store.get_result(f"r{sample_size}") == result


# Checks that an unknown identifier resolves to None.
def test_get_result_missing_returns_none(store: ResultDbStore) -> None:
    store.insert_result("known", make_result())

    assert store.get_result("unknown") is None


# Checks that paginated retrieval orders results by identifier.
def test_get_results_is_ordered_by_id(store: ResultDbStore) -> None:
    store.insert_result("b", make_result(experiment_name="b"))
    store.insert_result("a", make_result(experiment_name="a"))
    store.insert_result("c", make_result(experiment_name="c"))

    results = store.get_results(0, 10)

    assert [item.experiment_name for item in results] == ["a", "b", "c"]


# Checks that offset and limit are applied to the ordered result stream.
@pytest.mark.parametrize(
    ("offset", "limit", "expected"),
    [
        pytest.param(0, 2, ["a", "b"], id="first-page"),
        pytest.param(1, 2, ["b", "c"], id="second-page"),
        pytest.param(2, 5, ["c"], id="tail-page"),
        pytest.param(0, 0, [], id="empty-limit"),
        pytest.param(5, 5, [], id="offset-beyond-end"),
    ],
)
def test_get_results_applies_offset_and_limit(
    store: ResultDbStore, offset: int, limit: int, expected: list[str]
) -> None:
    for key in ("a", "b", "c"):
        store.insert_result(key, make_result(experiment_name=key))

    results = store.get_results(offset, limit)

    assert [item.experiment_name for item in results] == expected


# Checks that paginated retrieval on an empty store yields an empty list.
def test_get_results_on_empty_store_returns_empty_list(store: ResultDbStore) -> None:
    assert store.get_results(0, 10) == []
