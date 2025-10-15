from __future__ import annotations

from pathlib import Path

import pytest

from pysatl_experiment.persistence.model.time_complexity.time_complexity import TimeComplexityModel, TimeComplexityQuery
from pysatl_experiment.persistence.time_complexity.sqlite.sqlite import SQLiteTimeComplexityStorage


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "time_complexity.sqlite"


@pytest.fixture()
def storage(db_path: Path) -> SQLiteTimeComplexityStorage:
    store = SQLiteTimeComplexityStorage(str(db_path))
    store.init()
    return store


def test_guard_requires_init(db_path: Path) -> None:
    store = SQLiteTimeComplexityStorage(str(db_path))
    with pytest.raises(RuntimeError):
        _ = store.get_data(
            TimeComplexityQuery(
                criterion_code="crit_A",
                criterion_parameters=[0.1, 0.2],
                sample_size=10,
                monte_carlo_count=100,
            )
        )


def test_get_data_empty_returns_none(storage: SQLiteTimeComplexityStorage) -> None:
    query = TimeComplexityQuery(
        criterion_code="crit_A",
        criterion_parameters=[0.1, 0.2],
        sample_size=10,
        monte_carlo_count=100,
    )
    assert storage.get_data(query) is None


def test_insert_and_get(storage: SQLiteTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        experiment_id=123,
        criterion_code="crit_A",
        criterion_parameters=[0.1, 0.2],
        sample_size=10,
        monte_carlo_count=100,
        results_times=[1.0, 2.0, 3.0],
    )
    storage.insert_data(model)

    got = storage.get_data(
        TimeComplexityQuery(
            criterion_code="crit_A",
            criterion_parameters=[0.1, 0.2],
            sample_size=10,
            monte_carlo_count=100,
        )
    )

    assert got is not None
    assert got.experiment_id == model.experiment_id
    assert got.criterion_code == model.criterion_code
    assert got.criterion_parameters == model.criterion_parameters
    assert got.sample_size == model.sample_size
    assert got.monte_carlo_count == model.monte_carlo_count
    assert got.results_times == model.results_times


def test_delete_data(storage: SQLiteTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        experiment_id=7,
        criterion_code="crit_B",
        criterion_parameters=[0.3],
        sample_size=5,
        monte_carlo_count=50,
        results_times=[0.5, 0.6],
    )
    storage.insert_data(model)

    storage.delete_data(
        TimeComplexityQuery(
            criterion_code="crit_B",
            criterion_parameters=[0.3],
            sample_size=5,
            monte_carlo_count=50,
        )
    )

    assert (
        storage.get_data(
            TimeComplexityQuery(
                criterion_code="crit_B",
                criterion_parameters=[0.3],
                sample_size=5,
                monte_carlo_count=50,
            )
        )
        is None
    )
