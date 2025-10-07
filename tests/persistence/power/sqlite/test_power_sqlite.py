from __future__ import annotations

from pathlib import Path

import pytest

from pysatl_experiment.persistence.model.power.power import PowerModel, PowerQuery
from pysatl_experiment.persistence.power.sqlite.sqlite import SQLitePowerStorage


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "power.sqlite"


@pytest.fixture()
def storage(db_path: Path) -> SQLitePowerStorage:
    store = SQLitePowerStorage(str(db_path))
    store.init()
    return store


def test_guard_requires_init(db_path: Path) -> None:
    store = SQLitePowerStorage(str(db_path))
    with pytest.raises(RuntimeError):
        _ = store.get_data(
            PowerQuery(
                criterion_code="crit_A",
                criterion_parameters=[0.1, 0.2],
                sample_size=10,
                alternative_code="alt_A",
                alternative_parameters=[1.0],
                monte_carlo_count=100,
                significance_level=0.05,
            )
        )


def test_get_data_empty_returns_none(storage: SQLitePowerStorage) -> None:
    query = PowerQuery(
        criterion_code="crit_A",
        criterion_parameters=[0.1, 0.2],
        sample_size=10,
        alternative_code="alt_A",
        alternative_parameters=[1.0],
        monte_carlo_count=100,
        significance_level=0.05,
    )
    assert storage.get_data(query) is None


def test_insert_and_get(storage: SQLitePowerStorage) -> None:
    model = PowerModel(
        experiment_id=123,
        criterion_code="crit_A",
        criterion_parameters=[0.1, 0.2],
        sample_size=10,
        alternative_code="alt_A",
        alternative_parameters=[1.0],
        monte_carlo_count=100,
        significance_level=0.05,
        results_criteria=[True, False, True],
    )
    storage.insert_data(model)

    got = storage.get_data(
        PowerQuery(
            criterion_code="crit_A",
            criterion_parameters=[0.1, 0.2],
            sample_size=10,
            alternative_code="alt_A",
            alternative_parameters=[1.0],
            monte_carlo_count=100,
            significance_level=0.05,
        )
    )

    assert got is not None
    assert got.experiment_id == model.experiment_id
    assert got.criterion_code == model.criterion_code
    assert got.criterion_parameters == model.criterion_parameters
    assert got.sample_size == model.sample_size
    assert got.alternative_code == model.alternative_code
    assert got.alternative_parameters == model.alternative_parameters
    assert got.monte_carlo_count == model.monte_carlo_count
    assert got.significance_level == model.significance_level
    assert got.results_criteria == model.results_criteria


def test_delete_data(storage: SQLitePowerStorage) -> None:
    model = PowerModel(
        experiment_id=7,
        criterion_code="crit_B",
        criterion_parameters=[0.3],
        sample_size=5,
        alternative_code="alt_B",
        alternative_parameters=[2.0, 3.0],
        monte_carlo_count=50,
        significance_level=0.1,
        results_criteria=[False, False],
    )
    storage.insert_data(model)

    storage.delete_data(
        PowerQuery(
            criterion_code="crit_B",
            criterion_parameters=[0.3],
            sample_size=5,
            alternative_code="alt_B",
            alternative_parameters=[2.0, 3.0],
            monte_carlo_count=50,
            significance_level=0.1,
        )
    )

    assert (
        storage.get_data(
            PowerQuery(
                criterion_code="crit_B",
                criterion_parameters=[0.3],
                sample_size=5,
                alternative_code="alt_B",
                alternative_parameters=[2.0, 3.0],
                monte_carlo_count=50,
                significance_level=0.1,
            )
        )
        is None
    )
