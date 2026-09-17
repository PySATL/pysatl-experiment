"""Tests for SQLAlchemy time complexity storage implementation."""

from __future__ import annotations

from pathlib import Path

import pytest

from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel, TimeComplexityQuery
from pysatl_experiment.persistence.time_complexity_storage import AlchemyTimeComplexityStorage


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "time_complexity.sqlite"


@pytest.fixture()
def storage(db_path: Path) -> AlchemyTimeComplexityStorage:
    store = AlchemyTimeComplexityStorage(db_url="sqlite:///:memory:")
    store.init()
    return store


def test_guard_requires_init(db_path: Path) -> None:
    store = AlchemyTimeComplexityStorage(str(db_path))
    with pytest.raises(RuntimeError):
        _ = store.get_data(
            TimeComplexityQuery(
                experiment_name="experiment-a",
                criterion_code="crit_A",
                criterion_parameters={"alpha": 0.1, "beta": 0.2},
                sample_size=10,
                samples_count=100,
            )
        )


def test_get_data_empty_returns_none(storage: AlchemyTimeComplexityStorage) -> None:
    query = TimeComplexityQuery(
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters={"alpha": 0.1, "beta": 0.2},
        sample_size=10,
        samples_count=100,
    )
    assert storage.get_data(query) is None


def test_insert_and_get(storage: AlchemyTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters={"alpha": 0.1, "beta": 0.2},
        sample_size=10,
        samples_count=100,
        results_times=[1.0, 2.0, 3.0],
    )
    storage.insert_data(model)

    got = storage.get_data(
        TimeComplexityQuery(
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1, "beta": 0.2},
            sample_size=10,
            samples_count=100,
        )
    )

    assert got is not None
    assert got.experiment_name == model.experiment_name
    assert got.criterion_code == model.criterion_code
    assert got.criterion_parameters == model.criterion_parameters
    assert got.sample_size == model.sample_size
    assert got.samples_count == model.samples_count
    assert got.results_times == model.results_times


def test_bulk_insert_data(storage: AlchemyTimeComplexityStorage) -> None:
    models = [
        TimeComplexityModel(
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1},
            sample_size=10,
            samples_count=100,
            results_times=[1.0],
        ),
        TimeComplexityModel(
            experiment_name="experiment-b",
            criterion_code="crit_B",
            criterion_parameters={"alpha": 0.2},
            sample_size=20,
            samples_count=200,
            results_times=[2.0],
        ),
    ]

    storage.bulk_insert_data(models)

    for model in models:
        got = storage.get_data(
            TimeComplexityQuery(
                experiment_name=model.experiment_name,
                criterion_code=model.criterion_code,
                criterion_parameters=model.criterion_parameters,
                sample_size=model.sample_size,
                samples_count=model.samples_count,
            )
        )
        assert got == model


def test_bulk_insert_data_updates_existing_record(storage: AlchemyTimeComplexityStorage) -> None:
    storage.insert_data(
        TimeComplexityModel(
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1},
            sample_size=10,
            samples_count=100,
            results_times=[1.0],
        )
    )
    updated = TimeComplexityModel(
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters={"alpha": 0.1},
        sample_size=10,
        samples_count=100,
        results_times=[2.0, 3.0],
    )

    storage.bulk_insert_data([updated])

    got = storage.get_data(
        TimeComplexityQuery(
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1},
            sample_size=10,
            samples_count=100,
        )
    )
    assert got == updated


def test_get_data_filters_by_experiment_name(storage: AlchemyTimeComplexityStorage) -> None:
    storage.bulk_insert_data(
        [
            TimeComplexityModel(
                experiment_name="experiment-a",
                criterion_code="crit_A",
                criterion_parameters={"alpha": 0.1},
                sample_size=10,
                samples_count=100,
                results_times=[1.0],
            ),
            TimeComplexityModel(
                experiment_name="experiment-b",
                criterion_code="crit_A",
                criterion_parameters={"alpha": 0.1},
                sample_size=10,
                samples_count=100,
                results_times=[2.0],
            ),
        ]
    )

    got = storage.get_data(
        TimeComplexityQuery(
            experiment_name="experiment-b",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1},
            sample_size=10,
            samples_count=100,
        )
    )

    assert got is not None
    assert got.experiment_name == "experiment-b"
    assert got.results_times == [2.0]


def test_criterion_parameters_are_order_independent(storage: AlchemyTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters={"zeta": 2.0, "alpha": 1.0},
        sample_size=10,
        samples_count=100,
        results_times=[1.0],
    )
    storage.insert_data(model)

    got = storage.get_data(
        TimeComplexityQuery(
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 1.0, "zeta": 2.0},
            sample_size=10,
            samples_count=100,
        )
    )

    assert got is not None
    assert list(got.criterion_parameters) == ["alpha", "zeta"]
    assert got.results_times == [1.0]


def test_criterion_parameter_lists_are_normalized_in_storage(storage: AlchemyTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters=[0.1, 0.2],
        sample_size=10,
        samples_count=100,
        results_times=[1.0],
    )
    storage.insert_data(model)

    got = storage.get_data(
        TimeComplexityQuery(
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"0": 0.1, "1": 0.2},
            sample_size=10,
            samples_count=100,
        )
    )

    assert got is not None
    assert got.criterion_parameters == {"0": 0.1, "1": 0.2}
    assert got.results_times == [1.0]


def test_delete_data(storage: AlchemyTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        experiment_name="experiment-b",
        criterion_code="crit_B",
        criterion_parameters={"alpha": 0.3},
        sample_size=5,
        samples_count=50,
        results_times=[0.5, 0.6],
    )
    storage.insert_data(model)

    storage.delete_data(
        TimeComplexityQuery(
            experiment_name="experiment-b",
            criterion_code="crit_B",
            criterion_parameters={"alpha": 0.3},
            sample_size=5,
            samples_count=50,
        )
    )

    assert (
        storage.get_data(
            TimeComplexityQuery(
                experiment_name="experiment-b",
                criterion_code="crit_B",
                criterion_parameters={"alpha": 0.3},
                sample_size=5,
                samples_count=50,
            )
        )
        is None
    )
